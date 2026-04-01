import argparse
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from vexai.strategy import Action, Assignment, FieldState, MatchPhase, RobotState, TeamPlan, Zone, choose_plan


TOTAL_MATCH_SECONDS = 120
ISOLATION_SECONDS = 15


@dataclass(frozen=True)
class SimulationConfig:
    step_seconds: int = 5
    initial_long_blocks: int = 6
    initial_center_blocks: int = 6
    control_bonus_threat_times: Sequence[int] = ()
    alpha_link_fail_times: Sequence[int] = ()
    beta_link_fail_times: Sequence[int] = ()


@dataclass(frozen=True)
class RobotSimState:
    name: str
    linked: bool
    carried_blocks: int
    parked: bool


@dataclass(frozen=True)
class SimulationSnapshot:
    field: FieldState
    alpha: RobotSimState
    beta: RobotSimState
    alpha_plan: Assignment
    beta_plan: Assignment
    alliance_score: int
    opponent_score: int
    notes: Tuple[str, ...]


@dataclass(frozen=True)
class MatchReport:
    timeline: List[SimulationSnapshot]
    final_score: int
    final_opponent_score: int


def _phase_for_time(seconds_remaining: int) -> MatchPhase:
    if seconds_remaining > TOTAL_MATCH_SECONDS - ISOLATION_SECONDS:
        return MatchPhase.ISOLATION
    return MatchPhase.INTERACTION


def _zone_points(zone: Zone) -> int:
    if zone == Zone.LONG_GOAL:
        return 4
    if zone == Zone.CENTER_GOAL:
        return 3
    return 2


def _robot_for_strategy(robot: RobotSimState) -> RobotState:
    return RobotState(
        linked=robot.linked,
        carrying_blocks=robot.carried_blocks > 0,
        parked=robot.parked,
    )


def _copy_robot(robot: RobotSimState, *, linked=None, carried_blocks=None, parked=None) -> RobotSimState:
    return RobotSimState(
        name=robot.name,
        linked=robot.linked if linked is None else linked,
        carried_blocks=robot.carried_blocks if carried_blocks is None else carried_blocks,
        parked=robot.parked if parked is None else parked,
    )


def _apply_collect(robot: RobotSimState, zone: Zone, long_blocks: int, center_blocks: int) -> Tuple[RobotSimState, int, int, str]:
    if robot.parked:
        return robot, long_blocks, center_blocks, f"{robot.name} is parked and cannot collect."
    if robot.carried_blocks > 0:
        return robot, long_blocks, center_blocks, f"{robot.name} is already holding a block."

    if zone == Zone.LONG_GOAL and long_blocks > 0:
        return _copy_robot(robot, carried_blocks=1), long_blocks - 1, center_blocks, f"{robot.name} collected from long side."
    if zone == Zone.CENTER_GOAL and center_blocks > 0:
        return _copy_robot(robot, carried_blocks=1), long_blocks, center_blocks - 1, f"{robot.name} collected from center side."
    return robot, long_blocks, center_blocks, f"{robot.name} found no loose blocks in {zone.name}."


def _apply_score(robot: RobotSimState, assignment: Assignment) -> Tuple[RobotSimState, int, str]:
    if robot.parked:
        return robot, 0, f"{robot.name} is parked and cannot score."
    if robot.carried_blocks <= 0:
        return robot, 0, f"{robot.name} had nothing to score."

    points = robot.carried_blocks * _zone_points(assignment.zone)
    return _copy_robot(robot, carried_blocks=0), points, f"{robot.name} scored {points} points at {assignment.zone.name}."


def _apply_assignment(
    robot: RobotSimState,
    assignment: Assignment,
    long_blocks: int,
    center_blocks: int,
    control_bonus_threatened: bool,
) -> Tuple[RobotSimState, int, int, int, bool, str]:
    if assignment.action == Action.COLLECT_BLOCKS:
        robot, long_blocks, center_blocks, note = _apply_collect(robot, assignment.zone, long_blocks, center_blocks)
        return robot, long_blocks, center_blocks, 0, control_bonus_threatened, note

    if assignment.action == Action.SCORE_GOAL:
        robot, points, note = _apply_score(robot, assignment)
        return robot, long_blocks, center_blocks, points, control_bonus_threatened, note

    if assignment.action == Action.DEFEND_CONTROL_BONUS:
        return robot, long_blocks, center_blocks, 1, False, f"{robot.name} stabilized the control bonus."

    if assignment.action == Action.PARK:
        if robot.parked:
            return robot, long_blocks, center_blocks, 0, control_bonus_threatened, f"{robot.name} was already parked."
        return _copy_robot(robot, parked=True), long_blocks, center_blocks, 4, control_bonus_threatened, f"{robot.name} parked successfully."

    if assignment.action == Action.VERIFY_LINK:
        return _copy_robot(robot, linked=True), long_blocks, center_blocks, 0, control_bonus_threatened, f"{robot.name} recovered its link."

    return robot, long_blocks, center_blocks, 0, control_bonus_threatened, f"{robot.name} held position."


def simulate_match(config: SimulationConfig) -> MatchReport:
    timeline = []
    alpha = RobotSimState(name="Thor", linked=True, carried_blocks=0, parked=False)
    beta = RobotSimState(name="Loki", linked=True, carried_blocks=0, parked=False)
    alliance_score = 0
    opponent_score = 0
    loose_long = config.initial_long_blocks
    loose_center = config.initial_center_blocks
    control_bonus_threatened = False

    seconds_remaining = TOTAL_MATCH_SECONDS
    while seconds_remaining >= 0:
        phase = _phase_for_time(seconds_remaining)

        notes = []
        if phase == MatchPhase.INTERACTION and seconds_remaining in config.control_bonus_threat_times:
            control_bonus_threatened = True
            notes.append("Opponent pressure threatened the control bonus.")

        if seconds_remaining in config.alpha_link_fail_times:
            alpha = _copy_robot(alpha, linked=False)
            notes.append("Thor lost the partner link.")

        if seconds_remaining in config.beta_link_fail_times:
            beta = _copy_robot(beta, linked=False)
            notes.append("Loki lost the partner link.")

        field = FieldState(
            phase=phase,
            seconds_remaining=seconds_remaining,
            loose_blocks_long=loose_long,
            loose_blocks_center=loose_center,
            control_bonus_threatened=control_bonus_threatened,
        )
        plan = choose_plan(field, _robot_for_strategy(alpha), _robot_for_strategy(beta))

        if phase == MatchPhase.INTERACTION:
            opponent_score += 1
            if control_bonus_threatened:
                opponent_score += 1

        alpha, loose_long, loose_center, alpha_points, control_bonus_threatened, alpha_note = _apply_assignment(
            alpha,
            plan.alpha,
            loose_long,
            loose_center,
            control_bonus_threatened,
        )
        beta, loose_long, loose_center, beta_points, control_bonus_threatened, beta_note = _apply_assignment(
            beta,
            plan.beta,
            loose_long,
            loose_center,
            control_bonus_threatened,
        )

        alliance_score += alpha_points + beta_points
        notes.extend((alpha_note, beta_note))
        timeline.append(
            SimulationSnapshot(
                field=FieldState(
                    phase=phase,
                    seconds_remaining=seconds_remaining,
                    loose_blocks_long=loose_long,
                    loose_blocks_center=loose_center,
                    control_bonus_threatened=control_bonus_threatened,
                ),
                alpha=alpha,
                beta=beta,
                alpha_plan=plan.alpha,
                beta_plan=plan.beta,
                alliance_score=alliance_score,
                opponent_score=opponent_score,
                notes=tuple(notes),
            )
        )

        seconds_remaining -= config.step_seconds

    return MatchReport(
        timeline=timeline,
        final_score=alliance_score,
        final_opponent_score=opponent_score,
    )


def _format_snapshot(snapshot: SimulationSnapshot) -> str:
    return (
        f"T-{snapshot.field.seconds_remaining:>3}s "
        f"{snapshot.field.phase.name:<11} "
        f"Thor:{snapshot.alpha_plan.action.name:<20} "
        f"Loki:{snapshot.beta_plan.action.name:<20} "
        f"Score {snapshot.alliance_score}-{snapshot.opponent_score}"
    )


def format_report(report: MatchReport) -> str:
    lines = ["VEX AI Match Simulation", "========================", ""]
    for snapshot in report.timeline:
        lines.append(_format_snapshot(snapshot))
        for note in snapshot.notes:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append(f"Final score: alliance {report.final_score}, opponent {report.final_opponent_score}")
    return "\n".join(lines)


def _scenario_config(name: str) -> SimulationConfig:
    if name == "link-loss":
        return SimulationConfig(
            step_seconds=5,
            initial_long_blocks=5,
            initial_center_blocks=4,
            control_bonus_threat_times=(95, 70, 45),
            alpha_link_fail_times=(50,),
        )
    if name == "pressure":
        return SimulationConfig(
            step_seconds=5,
            initial_long_blocks=4,
            initial_center_blocks=6,
            control_bonus_threat_times=(100, 85, 70, 55),
        )
    return SimulationConfig(
        step_seconds=5,
        initial_long_blocks=5,
        initial_center_blocks=5,
        control_bonus_threat_times=(95, 60),
    )


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Run a stepped VEX AI match simulation.")
    parser.add_argument(
        "--scenario",
        choices=("default", "link-loss", "pressure"),
        default="default",
        help="Select a built-in match scenario.",
    )
    args = parser.parse_args(argv)

    report = simulate_match(_scenario_config(args.scenario))
    print(format_report(report))

