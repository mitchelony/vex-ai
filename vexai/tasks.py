from dataclasses import dataclass
from typing import Dict, Type

from vexai.planner import GoalTarget, IntentKind, RobotIntent
from vexai.robots import RobotName
from vexai.state import FieldRegion, LoadState, Pose2D, WorldState


WAYPOINTS = {
    (RobotName.THOR, FieldRegion.LONG_GOAL): Pose2D(1_200.0, 400.0, 0.0, 0, False),
    (RobotName.THOR, FieldRegion.CENTER_GOAL): Pose2D(800.0, 150.0, 0.0, 0, False),
    (RobotName.THOR, FieldRegion.PARK_ZONE): Pose2D(250.0, -200.0, 0.0, 0, False),
    (RobotName.THOR, FieldRegion.LINK_STATION): Pose2D(0.0, 0.0, 0.0, 0, False),
    (RobotName.LOKI, FieldRegion.LONG_GOAL): Pose2D(1_050.0, 350.0, 0.0, 0, False),
    (RobotName.LOKI, FieldRegion.CENTER_GOAL): Pose2D(650.0, 120.0, 0.0, 0, False),
    (RobotName.LOKI, FieldRegion.PARK_ZONE): Pose2D(180.0, -180.0, 0.0, 0, False),
    (RobotName.LOKI, FieldRegion.LINK_STATION): Pose2D(0.0, 0.0, 0.0, 0, False),
}


def get_region_waypoint(robot_name: RobotName, region: FieldRegion) -> Pose2D:
    return WAYPOINTS[(robot_name, region)]


@dataclass
class BaseTask:
    intent: RobotIntent
    created_at_ms: int
    robot_name: RobotName = RobotName.THOR
    min_hold_ms: int = 300
    timeout_ms: int = 3_000

    def enter(self, now_ms: int) -> None:
        self.created_at_ms = now_ms

    def update(self, world: WorldState, now_ms: int) -> None:
        return None

    def is_done(self, world: WorldState, now_ms: int) -> bool:
        return False

    def has_failed(self, world: WorldState, now_ms: int) -> bool:
        robot = world.thor if self.robot_name == RobotName.THOR else world.loki
        return robot.jammed or now_ms - self.created_at_ms > self.timeout_ms


class CollectTask(BaseTask):
    def is_done(self, world: WorldState, now_ms: int) -> bool:
        robot = world.thor if self.robot_name == RobotName.THOR else world.loki
        return robot.load_state != LoadState.EMPTY


class ScoreTask(BaseTask):
    def is_done(self, world: WorldState, now_ms: int) -> bool:
        robot = world.thor if self.robot_name == RobotName.THOR else world.loki
        return robot.load_state == LoadState.EMPTY


class VerifyLinkTask(BaseTask):
    def is_done(self, world: WorldState, now_ms: int) -> bool:
        robot = world.thor if self.robot_name == RobotName.THOR else world.loki
        return robot.linked and robot.link_age_ms <= self.timeout_ms


class HoldTask(BaseTask):
    pass


class ParkTask(BaseTask):
    def is_done(self, world: WorldState, now_ms: int) -> bool:
        robot = world.thor if self.robot_name == RobotName.THOR else world.loki
        return robot.parked


class DefendTask(BaseTask):
    pass


class ClearLaneTask(BaseTask):
    pass


TASK_TYPES: Dict[IntentKind, Type[BaseTask]] = {
    IntentKind.COLLECT_REGION: CollectTask,
    IntentKind.SCORE_LOW: ScoreTask,
    IntentKind.SCORE_HIGH: ScoreTask,
    IntentKind.VERIFY_LINK: VerifyLinkTask,
    IntentKind.HOLD_POSITION: HoldTask,
    IntentKind.PARK: ParkTask,
    IntentKind.DEFEND_CONTROL_BONUS: DefendTask,
    IntentKind.CLEAR_LANE: ClearLaneTask,
}


def task_from_intent(intent: RobotIntent, created_at_ms: int, robot_name: RobotName) -> BaseTask:
    task_class = TASK_TYPES[intent.task_kind]
    timeout_ms = 2_000 if intent.task_kind == IntentKind.VERIFY_LINK else 3_000
    return task_class(intent=intent, created_at_ms=created_at_ms, robot_name=robot_name, timeout_ms=timeout_ms)
