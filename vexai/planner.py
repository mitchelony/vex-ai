from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Optional, Set

from vexai.robots import RobotName
from vexai.state import FieldRegion, LoadState, MatchPhase, RobotWorldState, WorldState


class GoalTarget(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    HIGH = "HIGH"


class IntentKind(str, Enum):
    COLLECT_REGION = "COLLECT_REGION"
    SCORE_LOW = "SCORE_LOW"
    SCORE_HIGH = "SCORE_HIGH"
    DEFEND_CONTROL_BONUS = "DEFEND_CONTROL_BONUS"
    CLEAR_LANE = "CLEAR_LANE"
    VERIFY_LINK = "VERIFY_LINK"
    HOLD_POSITION = "HOLD_POSITION"
    PARK = "PARK"


class ReasonCode(str, Enum):
    SAFETY_LINK_LOSS = "safety_link_loss"
    SAFETY_STALE_POSE = "safety_stale_pose"
    OPENING_SCRIPT = "opening_script"
    LOADED_SCORE = "loaded_score"
    BONUS_DEFENSE = "bonus_defense"
    COLLECT_BEST_REGION = "collect_best_region"
    TASK_LOCK = "task_lock"
    ENDGAME_PARK = "endgame_park"


@dataclass(frozen=True)
class RobotIntent:
    task_kind: IntentKind
    target_region: FieldRegion = FieldRegion.NONE
    target_goal: GoalTarget = GoalTarget.NONE
    reason_code: str = ""
    score: float = 0.0
    reservation_key: Optional[str] = None


@dataclass(frozen=True)
class TeamIntentPlan:
    thor: RobotIntent
    loki: RobotIntent


@dataclass(frozen=True)
class PlannerConfig:
    endgame_park_seconds: int = 10
    bonus_defense_threshold: float = 0.7
    link_timeout_ms: int = 1_200
    task_lock_margin_ms: int = 0


DEFAULT_CONFIG = PlannerConfig()


def _reservation_for(intent: RobotIntent) -> Optional[str]:
    if intent.target_region == FieldRegion.NONE:
        return None
    if intent.target_goal == GoalTarget.NONE:
        return "%s:%s" % (intent.task_kind.value, intent.target_region.value)
    return "%s:%s:%s" % (
        intent.task_kind.value,
        intent.target_region.value,
        intent.target_goal.value,
    )


def _collect_region_for(robot_name: RobotName) -> FieldRegion:
    return FieldRegion.LONG_GOAL if robot_name == RobotName.THOR else FieldRegion.CENTER_GOAL


def _intent_from_locked_task(robot: RobotWorldState) -> RobotIntent:
    intent_kind = IntentKind(robot.current_intent_kind)
    target_region = robot.current_target_region or _collect_region_for(robot.name)
    target_goal = GoalTarget(robot.current_target_goal) if robot.current_target_goal else GoalTarget.NONE
    if intent_kind == IntentKind.SCORE_HIGH:
        target_goal = GoalTarget.HIGH
    elif intent_kind == IntentKind.SCORE_LOW:
        target_goal = GoalTarget.LOW
    intent = RobotIntent(
        task_kind=intent_kind,
        target_region=target_region,
        target_goal=target_goal,
        reason_code=ReasonCode.TASK_LOCK,
        score=50.0,
    )
    return RobotIntent(
        task_kind=intent.task_kind,
        target_region=intent.target_region,
        target_goal=intent.target_goal,
        reason_code=intent.reason_code,
        score=intent.score,
        reservation_key=_reservation_for(intent),
    )


def _base_collect_score(region_counts: Dict[FieldRegion, int], region: FieldRegion) -> float:
    return float(region_counts.get(region, 0))


def _travel_penalty(robot: RobotWorldState, region: FieldRegion) -> float:
    if robot.pose.stale:
        return 0.0
    target_positions = {
        FieldRegion.LONG_GOAL: (1_200.0, 400.0),
        FieldRegion.CENTER_GOAL: (700.0, 150.0),
        FieldRegion.PARK_ZONE: (200.0, -200.0),
        FieldRegion.LINK_STATION: (0.0, 0.0),
    }
    target_x, target_y = target_positions.get(region, (robot.pose.x_mm, robot.pose.y_mm))
    distance = abs(robot.pose.x_mm - target_x) + abs(robot.pose.y_mm - target_y)
    return distance / 1_000.0


def _make_intent(
    task_kind: IntentKind,
    target_region: FieldRegion,
    reason_code: str,
    score: float,
    target_goal: GoalTarget = GoalTarget.NONE,
) -> RobotIntent:
    intent = RobotIntent(
        task_kind=task_kind,
        target_region=target_region,
        target_goal=target_goal,
        reason_code=reason_code,
        score=score,
    )
    return RobotIntent(
        task_kind=intent.task_kind,
        target_region=intent.target_region,
        target_goal=intent.target_goal,
        reason_code=intent.reason_code,
        score=intent.score,
        reservation_key=_reservation_for(intent),
    )


def _opening_intent(robot: RobotWorldState) -> RobotIntent:
    return _make_intent(
        IntentKind.COLLECT_REGION,
        _collect_region_for(robot.name),
        ReasonCode.OPENING_SCRIPT,
        20.0,
    )


def _score_candidates(robot: RobotWorldState, reservations: Set[str], world: WorldState) -> Iterable[RobotIntent]:
    if robot.load_state not in (LoadState.ALLIANCE_HELD, LoadState.ALLIANCE_STORED):
        return []

    if robot.name == RobotName.THOR:
        intent = _make_intent(
            IntentKind.SCORE_HIGH,
            FieldRegion.LONG_GOAL,
            ReasonCode.LOADED_SCORE,
            12.0 + robot.storage.alliance_storage_count,
            GoalTarget.HIGH,
        )
        return [intent]

    high = _make_intent(
        IntentKind.SCORE_HIGH,
        FieldRegion.CENTER_GOAL,
        ReasonCode.LOADED_SCORE,
        8.0,
        GoalTarget.HIGH,
    )
    low = _make_intent(
        IntentKind.SCORE_LOW,
        FieldRegion.CENTER_GOAL,
        ReasonCode.LOADED_SCORE,
        8.5,
        GoalTarget.LOW,
    )
    return [high, low]


def _collect_candidates(robot: RobotWorldState, reservations: Set[str], world: WorldState) -> Iterable[RobotIntent]:
    candidates = []
    for region in (FieldRegion.LONG_GOAL, FieldRegion.CENTER_GOAL):
        reservation = "%s:%s" % (IntentKind.COLLECT_REGION.value, region.value)
        if reservation in reservations:
            continue
        score = 5.0 + _base_collect_score(world.field.loose_blocks_by_region, region)
        if robot.name == RobotName.THOR and region == FieldRegion.LONG_GOAL:
            score += 1.5
        if robot.name == RobotName.LOKI and region == FieldRegion.CENTER_GOAL:
            score += 1.5
        score -= _travel_penalty(robot, region)
        score *= max(0.3, min(robot.gps_confidence, robot.vision_confidence + 0.2))
        candidates.append(
            _make_intent(
                IntentKind.COLLECT_REGION,
                region,
                ReasonCode.COLLECT_BEST_REGION,
                score,
            )
        )
    return candidates


def _low_risk_partner_play(robot: RobotWorldState, reservations: Set[str], world: WorldState) -> RobotIntent:
    candidates = list(_collect_candidates(robot, reservations, world))
    if not candidates:
        return _make_intent(IntentKind.HOLD_POSITION, FieldRegion.CENTER_GOAL, ReasonCode.COLLECT_BEST_REGION, 0.0)
    return max(candidates, key=lambda intent: intent.score)


def _plan_robot(
    robot: RobotWorldState,
    teammate: RobotWorldState,
    world: WorldState,
    reservations: Set[str],
    now_ms: int,
    config: PlannerConfig,
) -> RobotIntent:
    if not robot.linked or robot.link_age_ms > config.link_timeout_ms:
        return _make_intent(IntentKind.VERIFY_LINK, FieldRegion.LINK_STATION, ReasonCode.SAFETY_LINK_LOSS, 100.0)

    if robot.pose.stale or robot.gps_confidence < 0.3:
        return _make_intent(IntentKind.HOLD_POSITION, FieldRegion.CENTER_GOAL, ReasonCode.SAFETY_STALE_POSE, 90.0)

    if robot.current_task_id and now_ms + config.task_lock_margin_ms < robot.task_locked_until_ms and robot.current_intent_kind:
        return _intent_from_locked_task(robot)

    if world.field.seconds_remaining <= config.endgame_park_seconds:
        return _make_intent(IntentKind.PARK, FieldRegion.PARK_ZONE, ReasonCode.ENDGAME_PARK, 95.0)

    if world.field.phase == MatchPhase.ISOLATION and world.field.opening_script_active:
        return _opening_intent(robot)

    if (
        robot.name == RobotName.THOR
        and world.field.phase == MatchPhase.INTERACTION
        and world.field.control_bonus_threat_score >= config.bonus_defense_threshold
    ):
        return _make_intent(
            IntentKind.DEFEND_CONTROL_BONUS,
            FieldRegion.LONG_GOAL,
            ReasonCode.BONUS_DEFENSE,
            40.0 + world.field.control_bonus_threat_score * 10.0,
        )

    candidates = list(_score_candidates(robot, reservations, world)) + list(_collect_candidates(robot, reservations, world))
    if robot.name == RobotName.THOR and robot.storage.opponent_denial_count_est < robot.storage.denial_capacity:
        candidates.append(
            _make_intent(
                IntentKind.CLEAR_LANE,
                FieldRegion.LONG_GOAL,
                ReasonCode.COLLECT_BEST_REGION,
                4.0,
            )
        )
    candidates.append(_make_intent(IntentKind.HOLD_POSITION, FieldRegion.CENTER_GOAL, ReasonCode.COLLECT_BEST_REGION, 0.5))

    valid_candidates = [candidate for candidate in candidates if candidate.reservation_key not in reservations]
    if not valid_candidates:
        return _make_intent(IntentKind.HOLD_POSITION, FieldRegion.CENTER_GOAL, ReasonCode.COLLECT_BEST_REGION, 0.0)
    return max(valid_candidates, key=lambda candidate: candidate.score)


def plan_team(world: WorldState, now_ms: int, config: PlannerConfig = DEFAULT_CONFIG) -> TeamIntentPlan:
    if not world.thor.linked and world.loki.linked:
        thor = _make_intent(IntentKind.VERIFY_LINK, FieldRegion.LINK_STATION, ReasonCode.SAFETY_LINK_LOSS, 100.0)
        loki = _low_risk_partner_play(world.loki, set(), world)
        return TeamIntentPlan(thor=thor, loki=loki)

    if not world.loki.linked and world.thor.linked:
        loki = _make_intent(IntentKind.VERIFY_LINK, FieldRegion.LINK_STATION, ReasonCode.SAFETY_LINK_LOSS, 100.0)
        thor = _low_risk_partner_play(world.thor, set(), world)
        return TeamIntentPlan(thor=thor, loki=loki)

    reservations = set()
    thor = _plan_robot(world.thor, world.loki, world, reservations, now_ms, config)
    if thor.reservation_key:
        reservations.add(thor.reservation_key)
    loki = _plan_robot(world.loki, world.thor, world, reservations, now_ms, config)
    if loki.reservation_key == thor.reservation_key and loki.task_kind == IntentKind.COLLECT_REGION:
        reservations.add(loki.reservation_key or "")
        loki = _make_intent(
            IntentKind.COLLECT_REGION,
            FieldRegion.CENTER_GOAL if loki.target_region == FieldRegion.LONG_GOAL else FieldRegion.LONG_GOAL,
            ReasonCode.COLLECT_BEST_REGION,
            max(0.0, loki.score - 1.0),
        )
    return TeamIntentPlan(thor=thor, loki=loki)
