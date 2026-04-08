import unittest

from vexai.planner import GoalTarget, IntentKind, RobotIntent
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
from vexai.tasks import CollectTask, ScoreTask, VerifyLinkTask, get_region_waypoint


def make_world(load_state: LoadState, *, linked: bool = True, link_age_ms: int = 0) -> WorldState:
    robot = RobotWorldState(
        name=RobotName.THOR,
        linked=linked,
        link_age_ms=link_age_ms,
        pose=Pose2D(x_mm=0.0, y_mm=0.0, heading_deg=0.0, timestamp_ms=0, stale=False),
        load_state=load_state,
        parked=False,
        current_task_id=None,
        current_intent_kind=None,
        task_locked_until_ms=0,
        gps_confidence=1.0,
        vision_confidence=1.0,
        jammed=False,
        storage=ThorStorageState(),
    )
    partner = RobotWorldState(
        name=RobotName.LOKI,
        linked=True,
        link_age_ms=0,
        pose=Pose2D(x_mm=500.0, y_mm=500.0, heading_deg=0.0, timestamp_ms=0, stale=False),
        load_state=LoadState.EMPTY,
        parked=False,
        current_task_id=None,
        current_intent_kind=None,
        task_locked_until_ms=0,
        gps_confidence=1.0,
        vision_confidence=1.0,
        jammed=False,
        storage=ThorStorageState(),
    )
    return WorldState(
        field=FieldWorldState(
            phase=MatchPhase.INTERACTION,
            seconds_remaining=60,
            loose_blocks_by_region={FieldRegion.LONG_GOAL: 3, FieldRegion.CENTER_GOAL: 2},
            control_bonus_threat_score=0.0,
            goal_pressure_by_region={FieldRegion.LONG_GOAL: 0.0, FieldRegion.CENTER_GOAL: 0.0},
            opening_script_active=False,
        ),
        thor=robot,
        loki=partner,
    )


class TaskTests(unittest.TestCase):
    def test_waypoint_targeting_uses_region_specific_safe_approach(self):
        waypoint = get_region_waypoint(RobotName.THOR, FieldRegion.LONG_GOAL)

        self.assertEqual(waypoint.x_mm, 1200.0)
        self.assertEqual(waypoint.y_mm, 400.0)

    def test_collect_task_completes_only_after_load_is_confirmed(self):
        task = CollectTask(
            RobotIntent(
                task_kind=IntentKind.COLLECT_REGION,
                target_region=FieldRegion.LONG_GOAL,
                reason_code="collect_best_region",
            ),
            created_at_ms=0,
        )

        self.assertFalse(task.is_done(make_world(LoadState.EMPTY), now_ms=500))
        self.assertTrue(task.is_done(make_world(LoadState.ALLIANCE_HELD), now_ms=500))

    def test_score_task_completes_after_load_clears(self):
        task = ScoreTask(
            RobotIntent(
                task_kind=IntentKind.SCORE_HIGH,
                target_region=FieldRegion.LONG_GOAL,
                target_goal=GoalTarget.HIGH,
                reason_code="loaded_score",
            ),
            created_at_ms=0,
        )

        self.assertFalse(task.is_done(make_world(LoadState.ALLIANCE_HELD), now_ms=500))
        self.assertTrue(task.is_done(make_world(LoadState.EMPTY), now_ms=500))

    def test_verify_link_task_recovers_or_times_out(self):
        task = VerifyLinkTask(
            RobotIntent(
                task_kind=IntentKind.VERIFY_LINK,
                target_region=FieldRegion.LINK_STATION,
                reason_code="safety_link_loss",
            ),
            created_at_ms=0,
            timeout_ms=2_000,
        )

        self.assertTrue(task.is_done(make_world(LoadState.EMPTY, linked=True), now_ms=500))
        self.assertTrue(task.has_failed(make_world(LoadState.EMPTY, linked=False), now_ms=2_500))


if __name__ == "__main__":
    unittest.main()
