from dataclasses import dataclass
from enum import Enum, auto

from vexai.planner import GoalTarget, IntentKind, plan_team
from vexai.robots import RobotName
from vexai.state import (
    FieldRegion,
    FieldWorldState,
    LoadState,
    MatchPhase,
    Pose2D,
    RobotWorldState,
    ThorStorageState,
    WorldState,
)


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


def _zone_to_region(zone: Zone) -> FieldRegion:
    mapping = {
        Zone.LONG_GOAL: FieldRegion.LONG_GOAL,
        Zone.CENTER_GOAL: FieldRegion.CENTER_GOAL,
        Zone.PARK_ZONE: FieldRegion.PARK_ZONE,
        Zone.LINK_STATION: FieldRegion.LINK_STATION,
        Zone.NONE: FieldRegion.NONE,
    }
    return mapping[zone]


def _region_to_zone(region: FieldRegion) -> Zone:
    mapping = {
        FieldRegion.LONG_GOAL: Zone.LONG_GOAL,
        FieldRegion.CENTER_GOAL: Zone.CENTER_GOAL,
        FieldRegion.PARK_ZONE: Zone.PARK_ZONE,
        FieldRegion.LINK_STATION: Zone.LINK_STATION,
        FieldRegion.NONE: Zone.NONE,
    }
    return mapping[region]


def _load_state_from_legacy(robot: RobotState) -> LoadState:
    return LoadState.ALLIANCE_HELD if robot.carrying_blocks else LoadState.EMPTY


def _legacy_robot_world(name: RobotName, robot: RobotState) -> RobotWorldState:
    return RobotWorldState(
        name=name,
        linked=robot.linked,
        link_age_ms=0 if robot.linked else 2_000,
        pose=Pose2D(x_mm=0.0, y_mm=0.0, heading_deg=0.0, timestamp_ms=0, stale=False),
        load_state=_load_state_from_legacy(robot),
        parked=robot.parked,
        current_task_id=None,
        current_intent_kind=None,
        task_locked_until_ms=0,
        gps_confidence=1.0,
        vision_confidence=1.0,
        jammed=False,
        storage=ThorStorageState(),
    )


def _assignment_from_intent(intent, default_region: FieldRegion) -> Assignment:
    if intent.task_kind == IntentKind.COLLECT_REGION:
        return Assignment(Action.COLLECT_BLOCKS, _region_to_zone(intent.target_region or default_region))
    if intent.task_kind in (IntentKind.SCORE_LOW, IntentKind.SCORE_HIGH):
        return Assignment(Action.SCORE_GOAL, _region_to_zone(intent.target_region or default_region))
    if intent.task_kind == IntentKind.DEFEND_CONTROL_BONUS:
        return Assignment(Action.DEFEND_CONTROL_BONUS, _region_to_zone(intent.target_region))
    if intent.task_kind == IntentKind.PARK:
        return Assignment(Action.PARK, Zone.PARK_ZONE)
    if intent.task_kind == IntentKind.VERIFY_LINK:
        return Assignment(Action.VERIFY_LINK, Zone.LINK_STATION)
    return Assignment(Action.HOLD_POSITION, _region_to_zone(intent.target_region or default_region))


def choose_plan(field: FieldState, alpha: RobotState, beta: RobotState) -> TeamPlan:
    world = WorldState(
        field=FieldWorldState(
            phase=field.phase,
            seconds_remaining=field.seconds_remaining,
            loose_blocks_by_region={
                FieldRegion.LONG_GOAL: field.loose_blocks_long,
                FieldRegion.CENTER_GOAL: field.loose_blocks_center,
            },
            control_bonus_threat_score=1.0 if field.control_bonus_threatened else 0.0,
            goal_pressure_by_region={
                FieldRegion.LONG_GOAL: 1.0 if field.control_bonus_threatened else 0.0,
                FieldRegion.CENTER_GOAL: 0.0,
            },
            opening_script_active=field.phase == MatchPhase.ISOLATION and field.seconds_remaining >= 110,
        ),
        thor=_legacy_robot_world(RobotName.THOR, alpha),
        loki=_legacy_robot_world(RobotName.LOKI, beta),
    )
    team_intents = plan_team(world, now_ms=0)
    return TeamPlan(
        alpha=_assignment_from_intent(team_intents.thor, FieldRegion.LONG_GOAL),
        beta=_assignment_from_intent(team_intents.loki, FieldRegion.CENTER_GOAL),
    )
