from dataclasses import dataclass
from enum import Enum, auto


class MatchPhase(Enum):
    ISOLATION = auto()
    INTERACTION = auto()


class Action(Enum):
    COLLECT_BLOCKS = auto()
    SCORE_GOAL = auto()
    DEFEND_CONTROL_BONUS = auto()
    PARK = auto()
    HOLD_POSITION = auto()
    VERIFY_LINK = auto()


class Zone(Enum):
    LONG_GOAL = auto()
    CENTER_GOAL = auto()
    PARK_ZONE = auto()
    LINK_STATION = auto()
    NONE = auto()


@dataclass(frozen=True)
class FieldState:
    phase: MatchPhase
    seconds_remaining: int
    loose_blocks_long: int
    loose_blocks_center: int
    control_bonus_threatened: bool


@dataclass(frozen=True)
class RobotState:
    linked: bool
    carrying_blocks: bool
    parked: bool


@dataclass(frozen=True)
class Assignment:
    action: Action
    zone: Zone


@dataclass(frozen=True)
class TeamPlan:
    alpha: Assignment
    beta: Assignment


def _collect_long() -> Assignment:
    return Assignment(Action.COLLECT_BLOCKS, Zone.LONG_GOAL)


def _collect_center() -> Assignment:
    return Assignment(Action.COLLECT_BLOCKS, Zone.CENTER_GOAL)


def choose_plan(field: FieldState, alpha: RobotState, beta: RobotState) -> TeamPlan:
    if not alpha.linked or not beta.linked:
        recovery = TeamPlan(
            alpha=Assignment(Action.HOLD_POSITION, Zone.CENTER_GOAL),
            beta=Assignment(Action.HOLD_POSITION, Zone.CENTER_GOAL),
        )

        if not alpha.linked:
            recovery = TeamPlan(
                alpha=Assignment(Action.VERIFY_LINK, Zone.LINK_STATION),
                beta=recovery.beta,
            )

        if not beta.linked:
            recovery = TeamPlan(
                alpha=recovery.alpha,
                beta=Assignment(Action.VERIFY_LINK, Zone.LINK_STATION),
            )

        return recovery

    if field.seconds_remaining <= 10:
        park = Assignment(Action.PARK, Zone.PARK_ZONE)
        return TeamPlan(alpha=park, beta=park)

    if field.phase == MatchPhase.INTERACTION and field.control_bonus_threatened:
        return TeamPlan(
            alpha=Assignment(Action.DEFEND_CONTROL_BONUS, Zone.LONG_GOAL),
            beta=_collect_center(),
        )

    alpha_task = Assignment(Action.SCORE_GOAL, Zone.LONG_GOAL) if alpha.carrying_blocks else _collect_long()
    beta_task = Assignment(Action.SCORE_GOAL, Zone.CENTER_GOAL) if beta.carrying_blocks else _collect_center()

    if field.phase == MatchPhase.ISOLATION:
        return TeamPlan(alpha=alpha_task, beta=beta_task)

    if field.loose_blocks_center > field.loose_blocks_long and not beta.carrying_blocks:
        beta_task = _collect_center()

    return TeamPlan(alpha=alpha_task, beta=beta_task)
