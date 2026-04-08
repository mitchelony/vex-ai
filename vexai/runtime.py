from dataclasses import dataclass, field
from typing import Optional

from vexai.link import decode_packet, encode_packet
from vexai.planner import TeamIntentPlan, plan_team
from vexai.robots import RobotName
from vexai.state import (
    BuiltWorldState,
    CalibrationProfile,
    FieldEstimateMemory,
    LocalSensorFrame,
    MechanismMemory,
    PartnerTelemetry,
    build_world_state,
)
from vexai.tasks import BaseTask, task_from_intent
from vexai.telemetry import MemoryReplayBuffer


@dataclass
class RuntimeState:
    mechanism_memory: MechanismMemory = field(default_factory=MechanismMemory)
    field_memory: FieldEstimateMemory = field(default_factory=FieldEstimateMemory)
    active_task: Optional[BaseTask] = None
    telemetry_buffer: MemoryReplayBuffer = field(default_factory=MemoryReplayBuffer)


@dataclass(frozen=True)
class CycleResult:
    built_world: BuiltWorldState
    plan: TeamIntentPlan
    active_task: BaseTask
    partner_packet: str
    log_record: dict


def _intent_for_local_robot(plan: TeamIntentPlan, robot_name: RobotName):
    return plan.thor if robot_name == RobotName.THOR else plan.loki


def run_cycle(
    local_frame: LocalSensorFrame,
    runtime_state: RuntimeState,
    partner_packet: Optional[str] = None,
    calibration: Optional[CalibrationProfile] = None,
    logger=None,
) -> CycleResult:
    partner = decode_packet(partner_packet) if partner_packet else None
    built = build_world_state(
        local_frame=local_frame,
        local_memory=runtime_state.mechanism_memory,
        field_memory=runtime_state.field_memory,
        partner=partner,
        calibration=calibration,
    )
    plan = plan_team(built.world, now_ms=local_frame.timestamp_ms)
    local_intent = _intent_for_local_robot(plan, local_frame.robot)

    active_task = runtime_state.active_task
    if (
        active_task is None
        or active_task.intent.task_kind != local_intent.task_kind
        or active_task.is_done(built.world, local_frame.timestamp_ms)
        or active_task.has_failed(built.world, local_frame.timestamp_ms)
    ):
        active_task = task_from_intent(local_intent, local_frame.timestamp_ms, local_frame.robot)

    local_robot = built.world.thor if local_frame.robot == RobotName.THOR else built.world.loki
    telemetry = PartnerTelemetry(
        robot=local_frame.robot,
        timestamp_ms=local_frame.timestamp_ms,
        x_mm=local_robot.pose.x_mm,
        y_mm=local_robot.pose.y_mm,
        heading_deg=local_robot.pose.heading_deg,
        load_state=local_robot.load_state,
        intent_kind=local_intent.task_kind.value,
        target_region=local_intent.target_region,
        health_flags=(
            "gps_stale" if local_robot.pose.stale else "gps_ok",
            "jammed" if local_robot.jammed else "healthy",
        ),
    )
    partner_packet_out = encode_packet(telemetry)
    log_record = {
        "t_ms": local_frame.timestamp_ms,
        "robot_local": local_frame.robot.name.lower(),
        "field": {
            "phase": built.world.field.phase.value,
            "seconds_remaining": built.world.field.seconds_remaining,
            "loose_blocks_by_region": {
                region.value: count for region, count in built.world.field.loose_blocks_by_region.items()
            },
        },
        "thor": {
            "pose": {
                "x_mm": built.world.thor.pose.x_mm,
                "y_mm": built.world.thor.pose.y_mm,
                "heading_deg": built.world.thor.pose.heading_deg,
            },
            "load_state": built.world.thor.load_state.value,
            "denial_estimate": built.world.thor.storage.opponent_denial_count_est,
        },
        "loki": {
            "pose": {
                "x_mm": built.world.loki.pose.x_mm,
                "y_mm": built.world.loki.pose.y_mm,
                "heading_deg": built.world.loki.pose.heading_deg,
            },
            "load_state": built.world.loki.load_state.value,
        },
        "link_status": {
            "thor": built.world.thor.linked,
            "loki": built.world.loki.linked,
        },
        "planner": {
            "intent_local": local_intent.task_kind.value,
            "reason_local": local_intent.reason_code,
        },
        "confidence": {
            "gps": local_robot.gps_confidence,
            "vision": local_robot.vision_confidence,
        },
    }
    runtime_state.mechanism_memory = built.mechanism_memory
    runtime_state.field_memory = built.field_memory
    runtime_state.active_task = active_task
    runtime_state.telemetry_buffer.append(log_record)
    if logger is not None:
        logger.write(log_record)
    return CycleResult(
        built_world=built,
        plan=plan,
        active_task=active_task,
        partner_packet=partner_packet_out,
        log_record=log_record,
    )
