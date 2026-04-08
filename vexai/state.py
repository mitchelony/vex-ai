from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

from vexai.robots import RobotName


class MatchPhase(str, Enum):
    ISOLATION = "ISOLATION"
    INTERACTION = "INTERACTION"


class FieldRegion(str, Enum):
    LONG_GOAL = "LONG_GOAL"
    CENTER_GOAL = "CENTER_GOAL"
    PARK_ZONE = "PARK_ZONE"
    LINK_STATION = "LINK_STATION"
    NONE = "NONE"


class LoadState(str, Enum):
    EMPTY = "EMPTY"
    ALLIANCE_HELD = "ALLIANCE_HELD"
    OPPONENT_HELD = "OPPONENT_HELD"
    ALLIANCE_STORED = "ALLIANCE_STORED"


class RouteTarget(str, Enum):
    NONE = "NONE"
    STORAGE = "STORAGE"
    DENIAL = "DENIAL"
    SCORE = "SCORE"


@dataclass(frozen=True)
class CalibrationProfile:
    x_offset_mm: float = 0.0
    y_offset_mm: float = 0.0
    heading_offset_deg: float = 0.0
    gps_stale_after_ms: int = 1_000
    max_field_coordinate_mm: float = 5_000.0
    optical_confirmation_threshold: int = 2
    partner_timeout_ms: int = 1_200


@dataclass(frozen=True)
class Pose2D:
    x_mm: float
    y_mm: float
    heading_deg: float
    timestamp_ms: int
    stale: bool = False


@dataclass(frozen=True)
class ThorStorageState:
    alliance_storage_count: int = 0
    opponent_denial_count_est: int = 0
    denial_capacity: int = 0
    denial_confidence: float = 0.0


@dataclass(frozen=True)
class RobotWorldState:
    name: RobotName
    linked: bool
    link_age_ms: int
    pose: Pose2D
    load_state: LoadState
    parked: bool
    current_task_id: Optional[str]
    current_intent_kind: Optional[str]
    task_locked_until_ms: int
    gps_confidence: float
    vision_confidence: float
    jammed: bool
    storage: ThorStorageState = field(default_factory=ThorStorageState)
    current_target_region: Optional[FieldRegion] = None
    current_target_goal: Optional[str] = None


@dataclass(frozen=True)
class FieldWorldState:
    phase: MatchPhase
    seconds_remaining: int
    loose_blocks_by_region: Dict[FieldRegion, int]
    control_bonus_threat_score: float
    goal_pressure_by_region: Dict[FieldRegion, float]
    opening_script_active: bool


@dataclass(frozen=True)
class WorldState:
    field: FieldWorldState
    thor: RobotWorldState
    loki: RobotWorldState


@dataclass(frozen=True)
class PartnerTelemetry:
    robot: RobotName
    timestamp_ms: int
    x_mm: float
    y_mm: float
    heading_deg: float
    load_state: LoadState
    intent_kind: Optional[str]
    target_region: FieldRegion
    health_flags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalSensorFrame:
    robot: RobotName
    timestamp_ms: int
    phase: MatchPhase
    seconds_remaining: int
    gps_x_mm: Optional[float] = None
    gps_y_mm: Optional[float] = None
    gps_heading_deg: Optional[float] = None
    gps_timestamp_ms: Optional[int] = None
    optical_color: str = "unknown"
    optical_has_object: bool = False
    ai_blocks_by_region: Dict[FieldRegion, int] = field(default_factory=dict)
    goal_pressure_by_region: Dict[FieldRegion, float] = field(default_factory=dict)
    control_bonus_pressure: float = 0.0
    linked: bool = True
    link_age_ms: int = 0
    parked: bool = False
    jammed: bool = False
    vision_confidence: float = 1.0
    route_target: RouteTarget = RouteTarget.NONE
    opening_script_active: Optional[bool] = None
    current_task_id: Optional[str] = None
    current_intent_kind: Optional[str] = None
    current_target_region: Optional[FieldRegion] = None
    current_target_goal: Optional[str] = None
    task_locked_until_ms: int = 0


@dataclass(frozen=True)
class MechanismMemory:
    alliance_storage_count: int = 0
    opponent_denial_count_est: int = 0
    denial_capacity: int = 3
    denial_confidence: float = 0.0
    optical_streak_color: str = "unknown"
    optical_streak_count: int = 0
    confirmed_load_state: LoadState = LoadState.EMPTY


@dataclass(frozen=True)
class FieldEstimateMemory:
    loose_blocks_by_region: Dict[FieldRegion, int] = field(
        default_factory=lambda: {
            FieldRegion.LONG_GOAL: 0,
            FieldRegion.CENTER_GOAL: 0,
        }
    )
    goal_pressure_by_region: Dict[FieldRegion, float] = field(
        default_factory=lambda: {
            FieldRegion.LONG_GOAL: 0.0,
            FieldRegion.CENTER_GOAL: 0.0,
        }
    )


@dataclass(frozen=True)
class BuiltWorldState:
    world: WorldState
    mechanism_memory: MechanismMemory
    field_memory: FieldEstimateMemory


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _normalize_heading(heading_deg: float) -> float:
    return heading_deg % 360.0


def _normalize_optical_color(color_name: str) -> str:
    return (color_name or "unknown").strip().lower()


def _default_pose(timestamp_ms: int) -> Pose2D:
    return Pose2D(x_mm=0.0, y_mm=0.0, heading_deg=0.0, timestamp_ms=timestamp_ms, stale=True)


def _build_pose(frame: LocalSensorFrame, calibration: CalibrationProfile) -> Tuple[Pose2D, float]:
    if frame.gps_timestamp_ms is None:
        return _default_pose(frame.timestamp_ms), 0.0

    if frame.gps_x_mm is None or frame.gps_y_mm is None or frame.gps_heading_deg is None:
        return _default_pose(frame.timestamp_ms), 0.0

    age_ms = frame.timestamp_ms - frame.gps_timestamp_ms
    stale = age_ms > calibration.gps_stale_after_ms
    sane = (
        abs(frame.gps_x_mm) <= calibration.max_field_coordinate_mm
        and abs(frame.gps_y_mm) <= calibration.max_field_coordinate_mm
    )
    if not sane:
        stale = True

    pose = Pose2D(
        x_mm=frame.gps_x_mm + calibration.x_offset_mm,
        y_mm=frame.gps_y_mm + calibration.y_offset_mm,
        heading_deg=_normalize_heading(frame.gps_heading_deg + calibration.heading_offset_deg),
        timestamp_ms=frame.gps_timestamp_ms,
        stale=stale,
    )
    confidence = 0.95 if not stale and sane else 0.2
    return pose, confidence


def _update_mechanism_memory(
    frame: LocalSensorFrame,
    memory: MechanismMemory,
    calibration: CalibrationProfile,
) -> MechanismMemory:
    color = _normalize_optical_color(frame.optical_color)
    streak_color = memory.optical_streak_color
    streak_count = memory.optical_streak_count
    confirmed_load_state = memory.confirmed_load_state
    alliance_storage_count = memory.alliance_storage_count
    denial_count = memory.opponent_denial_count_est
    denial_confidence = memory.denial_confidence

    if not frame.optical_has_object or color == "unknown":
        return MechanismMemory(
            alliance_storage_count=alliance_storage_count,
            opponent_denial_count_est=denial_count,
            denial_capacity=memory.denial_capacity,
            denial_confidence=_clamp(denial_confidence - 0.05, 0.0, 1.0),
            optical_streak_color="unknown",
            optical_streak_count=0,
            confirmed_load_state=LoadState.EMPTY if frame.route_target == RouteTarget.SCORE else confirmed_load_state,
        )

    if color == streak_color:
        streak_count += 1
    else:
        streak_color = color
        streak_count = 1

    if streak_count >= calibration.optical_confirmation_threshold:
        if color == "alliance":
            confirmed_load_state = LoadState.ALLIANCE_HELD
            if frame.route_target == RouteTarget.STORAGE and streak_count == calibration.optical_confirmation_threshold:
                alliance_storage_count += 1
                confirmed_load_state = LoadState.ALLIANCE_STORED
        elif color == "opponent":
            confirmed_load_state = LoadState.OPPONENT_HELD
            if frame.route_target == RouteTarget.DENIAL and streak_count == calibration.optical_confirmation_threshold:
                denial_count = min(memory.denial_capacity, denial_count + 1)
                denial_confidence = _clamp(denial_confidence + 0.3, 0.0, 1.0)

    return MechanismMemory(
        alliance_storage_count=alliance_storage_count,
        opponent_denial_count_est=denial_count,
        denial_capacity=memory.denial_capacity,
        denial_confidence=_clamp(denial_confidence, 0.0, 1.0),
        optical_streak_color=streak_color,
        optical_streak_count=streak_count,
        confirmed_load_state=confirmed_load_state,
    )


def _effective_load_state(robot_name: RobotName, memory: MechanismMemory) -> LoadState:
    if robot_name == RobotName.THOR and memory.alliance_storage_count > 0:
        return LoadState.ALLIANCE_STORED
    return memory.confirmed_load_state


def _update_field_memory(frame: LocalSensorFrame, field_memory: FieldEstimateMemory) -> FieldEstimateMemory:
    loose_blocks = {}
    for region in (FieldRegion.LONG_GOAL, FieldRegion.CENTER_GOAL):
        if region in frame.ai_blocks_by_region:
            loose_blocks[region] = max(0, int(frame.ai_blocks_by_region[region]))
        else:
            loose_blocks[region] = max(0, field_memory.loose_blocks_by_region.get(region, 0) - 1)

    goal_pressure = {}
    for region in (FieldRegion.LONG_GOAL, FieldRegion.CENTER_GOAL):
        if region in frame.goal_pressure_by_region:
            goal_pressure[region] = _clamp(float(frame.goal_pressure_by_region[region]), 0.0, 1.0)
        else:
            goal_pressure[region] = _clamp(field_memory.goal_pressure_by_region.get(region, 0.0) * 0.9, 0.0, 1.0)

    return FieldEstimateMemory(
        loose_blocks_by_region=loose_blocks,
        goal_pressure_by_region=goal_pressure,
    )


def _robot_from_partner(
    robot_name: RobotName,
    timestamp_ms: int,
    partner: Optional[PartnerTelemetry],
    calibration: CalibrationProfile,
) -> RobotWorldState:
    if partner is None or partner.robot != robot_name:
        return RobotWorldState(
            name=robot_name,
            linked=False,
            link_age_ms=calibration.partner_timeout_ms,
            pose=_default_pose(timestamp_ms),
            load_state=LoadState.EMPTY,
            parked=False,
            current_task_id=None,
            current_intent_kind=None,
            task_locked_until_ms=0,
            gps_confidence=0.0,
            vision_confidence=0.0,
            jammed=False,
        )

    link_age_ms = max(0, timestamp_ms - partner.timestamp_ms)
    linked = link_age_ms <= calibration.partner_timeout_ms
    return RobotWorldState(
        name=robot_name,
        linked=linked,
        link_age_ms=link_age_ms,
        pose=Pose2D(
            x_mm=partner.x_mm,
            y_mm=partner.y_mm,
            heading_deg=_normalize_heading(partner.heading_deg),
            timestamp_ms=partner.timestamp_ms,
            stale=not linked,
        ),
        load_state=partner.load_state,
        parked=False,
        current_task_id=None,
        current_intent_kind=partner.intent_kind,
        task_locked_until_ms=0,
        gps_confidence=0.7 if linked else 0.0,
        vision_confidence=0.0,
        jammed="jammed" in partner.health_flags,
        current_target_region=partner.target_region,
    )


def build_world_state(
    local_frame: LocalSensorFrame,
    local_memory: MechanismMemory,
    field_memory: FieldEstimateMemory,
    partner: Optional[PartnerTelemetry] = None,
    calibration: Optional[CalibrationProfile] = None,
) -> BuiltWorldState:
    calibration = calibration or CalibrationProfile()
    updated_memory = _update_mechanism_memory(local_frame, local_memory, calibration)
    updated_field_memory = _update_field_memory(local_frame, field_memory)
    pose, gps_confidence = _build_pose(local_frame, calibration)
    storage_state = ThorStorageState(
        alliance_storage_count=updated_memory.alliance_storage_count,
        opponent_denial_count_est=updated_memory.opponent_denial_count_est,
        denial_capacity=updated_memory.denial_capacity,
        denial_confidence=updated_memory.denial_confidence,
    )
    local_robot = RobotWorldState(
        name=local_frame.robot,
        linked=local_frame.linked,
        link_age_ms=local_frame.link_age_ms,
        pose=pose,
        load_state=_effective_load_state(local_frame.robot, updated_memory),
        parked=local_frame.parked,
        current_task_id=local_frame.current_task_id,
        current_intent_kind=local_frame.current_intent_kind,
        task_locked_until_ms=local_frame.task_locked_until_ms,
        gps_confidence=gps_confidence,
        vision_confidence=_clamp(local_frame.vision_confidence, 0.0, 1.0),
        jammed=local_frame.jammed,
        storage=storage_state,
        current_target_region=local_frame.current_target_region,
        current_target_goal=local_frame.current_target_goal,
    )

    partner_name = RobotName.LOKI if local_frame.robot == RobotName.THOR else RobotName.THOR
    partner_robot = _robot_from_partner(partner_name, local_frame.timestamp_ms, partner, calibration)

    if local_frame.robot == RobotName.THOR:
        thor = local_robot
        loki = partner_robot
    else:
        thor = partner_robot
        loki = local_robot

    opening_script_active = (
        local_frame.opening_script_active
        if local_frame.opening_script_active is not None
        else local_frame.phase == MatchPhase.ISOLATION and local_frame.seconds_remaining >= 110
    )
    world = WorldState(
        field=FieldWorldState(
            phase=local_frame.phase,
            seconds_remaining=local_frame.seconds_remaining,
            loose_blocks_by_region=dict(updated_field_memory.loose_blocks_by_region),
            control_bonus_threat_score=_clamp(local_frame.control_bonus_pressure, 0.0, 1.0),
            goal_pressure_by_region=dict(updated_field_memory.goal_pressure_by_region),
            opening_script_active=opening_script_active,
        ),
        thor=thor,
        loki=loki,
    )
    return BuiltWorldState(
        world=world,
        mechanism_memory=updated_memory,
        field_memory=updated_field_memory,
    )
