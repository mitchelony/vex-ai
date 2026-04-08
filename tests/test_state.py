import unittest

from vexai.robots import RobotName
from vexai.state import (
    CalibrationProfile,
    FieldEstimateMemory,
    FieldRegion,
    LoadState,
    LocalSensorFrame,
    MatchPhase,
    MechanismMemory,
    RouteTarget,
    build_world_state,
)


class StateBuilderTests(unittest.TestCase):
    def test_repeated_optical_confirmation_promotes_load_state(self):
        memory = MechanismMemory(denial_capacity=3)
        first = LocalSensorFrame(
            robot=RobotName.THOR,
            timestamp_ms=100,
            phase=MatchPhase.INTERACTION,
            seconds_remaining=90,
            optical_color="alliance",
            optical_has_object=True,
        )
        second = LocalSensorFrame(
            robot=RobotName.THOR,
            timestamp_ms=140,
            phase=MatchPhase.INTERACTION,
            seconds_remaining=90,
            optical_color="alliance",
            optical_has_object=True,
        )

        built = build_world_state(
            local_frame=first,
            local_memory=memory,
            field_memory=FieldEstimateMemory(),
        )
        self.assertEqual(built.world.thor.load_state, LoadState.EMPTY)

        built = build_world_state(
            local_frame=second,
            local_memory=built.mechanism_memory,
            field_memory=built.field_memory,
        )
        self.assertEqual(built.world.thor.load_state, LoadState.ALLIANCE_HELD)

    def test_routed_opponent_balls_increment_denial_estimate_but_clamp_to_capacity(self):
        memory = MechanismMemory(denial_capacity=2, opponent_denial_count_est=1, denial_confidence=0.5)
        frame = LocalSensorFrame(
            robot=RobotName.THOR,
            timestamp_ms=200,
            phase=MatchPhase.INTERACTION,
            seconds_remaining=80,
            optical_color="opponent",
            optical_has_object=True,
            route_target=RouteTarget.DENIAL,
        )

        built = build_world_state(
            local_frame=frame,
            local_memory=memory,
            field_memory=FieldEstimateMemory(),
        )
        built = build_world_state(
            local_frame=frame,
            local_memory=built.mechanism_memory,
            field_memory=built.field_memory,
        )

        self.assertEqual(built.mechanism_memory.opponent_denial_count_est, 2)
        self.assertEqual(built.world.thor.storage.opponent_denial_count_est, 2)
        self.assertLessEqual(built.world.thor.storage.denial_confidence, 1.0)

    def test_stale_gps_marks_pose_stale_and_degrades_confidence(self):
        frame = LocalSensorFrame(
            robot=RobotName.LOKI,
            timestamp_ms=5_000,
            phase=MatchPhase.INTERACTION,
            seconds_remaining=60,
            gps_x_mm=200.0,
            gps_y_mm=300.0,
            gps_heading_deg=90.0,
            gps_timestamp_ms=3_000,
        )

        built = build_world_state(
            local_frame=frame,
            local_memory=MechanismMemory(),
            field_memory=FieldEstimateMemory(),
            calibration=CalibrationProfile(),
        )

        self.assertTrue(built.world.loki.pose.stale)
        self.assertLess(built.world.loki.gps_confidence, 0.5)

    def test_ai_observations_update_field_estimates_with_decay(self):
        memory = FieldEstimateMemory(
            loose_blocks_by_region={
                FieldRegion.LONG_GOAL: 5,
                FieldRegion.CENTER_GOAL: 4,
            }
        )
        frame = LocalSensorFrame(
            robot=RobotName.THOR,
            timestamp_ms=1_000,
            phase=MatchPhase.INTERACTION,
            seconds_remaining=70,
            ai_blocks_by_region={FieldRegion.LONG_GOAL: 2},
        )

        built = build_world_state(
            local_frame=frame,
            local_memory=MechanismMemory(),
            field_memory=memory,
        )

        self.assertEqual(built.world.field.loose_blocks_by_region[FieldRegion.LONG_GOAL], 2)
        self.assertGreaterEqual(
            built.world.field.loose_blocks_by_region[FieldRegion.CENTER_GOAL],
            3,
        )


if __name__ == "__main__":
    unittest.main()
