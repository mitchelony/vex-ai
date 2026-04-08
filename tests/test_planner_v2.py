import unittest
from typing import Optional

from vexai.planner import GoalTarget, IntentKind, ReasonCode, plan_team
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


def make_robot(
    name: RobotName,
    *,
    linked: bool = True,
    link_age_ms: int = 0,
    load_state: LoadState = LoadState.EMPTY,
    parked: bool = False,
    stale_pose: bool = False,
    current_task_id: Optional[str] = None,
    current_intent_kind: Optional[str] = None,
    task_locked_until_ms: int = 0,
) -> RobotWorldState:
    return RobotWorldState(
        name=name,
        linked=linked,
        link_age_ms=link_age_ms,
        pose=Pose2D(x_mm=100.0, y_mm=100.0, heading_deg=0.0, timestamp_ms=1_000, stale=stale_pose),
        load_state=load_state,
        parked=parked,
        current_task_id=current_task_id,
        current_intent_kind=current_intent_kind,
        task_locked_until_ms=task_locked_until_ms,
        gps_confidence=0.9 if not stale_pose else 0.2,
        vision_confidence=0.8,
        jammed=False,
        storage=ThorStorageState(),
    )


def make_world(
    thor: RobotWorldState,
    loki: RobotWorldState,
    *,
    phase: MatchPhase = MatchPhase.INTERACTION,
    seconds_remaining: int = 60,
    long_blocks: int = 4,
    center_blocks: int = 4,
    threat: float = 0.0,
    opening_script_active: bool = False,
) -> WorldState:
    return WorldState(
        field=FieldWorldState(
            phase=phase,
            seconds_remaining=seconds_remaining,
            loose_blocks_by_region={
                FieldRegion.LONG_GOAL: long_blocks,
                FieldRegion.CENTER_GOAL: center_blocks,
            },
            control_bonus_threat_score=threat,
            goal_pressure_by_region={
                FieldRegion.LONG_GOAL: threat,
                FieldRegion.CENTER_GOAL: 0.0,
            },
            opening_script_active=opening_script_active,
        ),
        thor=thor,
        loki=loki,
    )


class PlannerTests(unittest.TestCase):
    def test_stale_pose_degrades_to_hold_position(self):
        world = make_world(
            make_robot(RobotName.THOR, stale_pose=True),
            make_robot(RobotName.LOKI),
        )

        plan = plan_team(world, now_ms=1_000)

        self.assertEqual(plan.thor.task_kind, IntentKind.HOLD_POSITION)
        self.assertEqual(plan.thor.reason_code, ReasonCode.SAFETY_STALE_POSE)

    def test_link_loss_allows_partner_to_continue_low_risk_collect(self):
        world = make_world(
            make_robot(RobotName.THOR, linked=False, link_age_ms=2_000),
            make_robot(RobotName.LOKI),
            long_blocks=1,
            center_blocks=3,
        )

        plan = plan_team(world, now_ms=2_000)

        self.assertEqual(plan.thor.task_kind, IntentKind.VERIFY_LINK)
        self.assertEqual(plan.loki.task_kind, IntentKind.COLLECT_REGION)
        self.assertEqual(plan.loki.target_region, FieldRegion.CENTER_GOAL)

    def test_opening_script_overrides_normal_reactive_scoring(self):
        world = make_world(
            make_robot(RobotName.THOR, load_state=LoadState.ALLIANCE_HELD),
            make_robot(RobotName.LOKI),
            phase=MatchPhase.ISOLATION,
            seconds_remaining=118,
            opening_script_active=True,
        )

        plan = plan_team(world, now_ms=500)

        self.assertEqual(plan.thor.reason_code, ReasonCode.OPENING_SCRIPT)
        self.assertEqual(plan.loki.reason_code, ReasonCode.OPENING_SCRIPT)

    def test_task_lock_prevents_oscillation(self):
        world = make_world(
            make_robot(
                RobotName.THOR,
                current_task_id="thor-lock",
                current_intent_kind=IntentKind.COLLECT_REGION.value,
                task_locked_until_ms=5_000,
            ),
            make_robot(RobotName.LOKI),
            long_blocks=0,
            center_blocks=5,
        )

        plan = plan_team(world, now_ms=1_000)

        self.assertEqual(plan.thor.reason_code, ReasonCode.TASK_LOCK)
        self.assertEqual(plan.thor.task_kind, IntentKind.COLLECT_REGION)

    def test_partner_reservation_prevents_duplicate_targets(self):
        world = make_world(
            make_robot(RobotName.THOR, load_state=LoadState.EMPTY),
            make_robot(RobotName.LOKI, load_state=LoadState.EMPTY),
            long_blocks=5,
            center_blocks=5,
        )

        plan = plan_team(world, now_ms=1_000)

        self.assertNotEqual(plan.thor.reservation_key, plan.loki.reservation_key)

    def test_bonus_threat_triggers_defense(self):
        world = make_world(
            make_robot(RobotName.THOR),
            make_robot(RobotName.LOKI),
            threat=0.9,
        )

        plan = plan_team(world, now_ms=1_000)

        self.assertEqual(plan.thor.task_kind, IntentKind.DEFEND_CONTROL_BONUS)
        self.assertEqual(plan.thor.reason_code, ReasonCode.BONUS_DEFENSE)

    def test_loaded_robot_prefers_high_score_target(self):
        world = make_world(
            make_robot(RobotName.THOR, load_state=LoadState.ALLIANCE_STORED),
            make_robot(RobotName.LOKI, load_state=LoadState.EMPTY),
        )

        plan = plan_team(world, now_ms=1_000)

        self.assertEqual(plan.thor.task_kind, IntentKind.SCORE_HIGH)
        self.assertEqual(plan.thor.target_goal, GoalTarget.HIGH)


if __name__ == "__main__":
    unittest.main()
