import unittest

from vexai.robots import (
    BallRoute,
    GoalHeight,
    IntakeStyle,
    RobotName,
    SensorSuite,
    ThorMode,
    get_robot_profile,
)


class RobotProfileTests(unittest.TestCase):
    def test_thor_profile_matches_big_bot_design(self):
        thor = get_robot_profile(RobotName.THOR)

        self.assertEqual(thor.name, RobotName.THOR)
        self.assertEqual(thor.intake_style, IntakeStyle.VERTICAL)
        self.assertEqual(thor.sensor_suite, SensorSuite(ai_front=True, gps_present=True, optical_in_intake=True))
        self.assertEqual(thor.ball_routes["alliance_intake"], BallRoute.TO_ALLIANCE_STORAGE)
        self.assertEqual(thor.ball_routes["opponent_intake"], BallRoute.TO_OPPONENT_HOLD)
        self.assertSetEqual(set(thor.supported_modes), {ThorMode.STORAGE, ThorMode.SCORING})
        self.assertSetEqual(set(thor.scoring_heights), {GoalHeight.LOW, GoalHeight.HIGH})
        self.assertTrue(thor.has_storage)

    def test_loki_profile_matches_direct_score_design(self):
        loki = get_robot_profile(RobotName.LOKI)

        self.assertEqual(loki.name, RobotName.LOKI)
        self.assertEqual(loki.intake_style, IntakeStyle.INCLINE)
        self.assertEqual(loki.sensor_suite, SensorSuite(ai_front=True, gps_present=True, optical_in_intake=True))
        self.assertFalse(loki.has_storage)
        self.assertDictEqual(loki.ball_routes, {"direct_score": BallRoute.DIRECT_SCORE_ONLY})
        self.assertListEqual(loki.supported_modes, [])
        self.assertSetEqual(set(loki.scoring_heights), {GoalHeight.LOW, GoalHeight.HIGH})


if __name__ == "__main__":
    unittest.main()
