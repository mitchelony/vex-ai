import unittest

from vexai.thor import (
    BallColor,
    ConveyorDirection,
    ScoreTarget,
    StorageRouting,
    route_ball_in_scoring_mode,
    route_ball_in_storage_mode,
)


class ThorStorageModeTests(unittest.TestCase):
    def test_alliance_ball_routes_into_alliance_storage(self):
        routing = route_ball_in_storage_mode(BallColor.RED, alliance_color=BallColor.RED)

        self.assertEqual(
            routing,
            StorageRouting(
                f_1_2=ConveyorDirection.RIGHT,
                f_3=ConveyorDirection.RIGHT,
                f_4=ConveyorDirection.LEFT,
                b_1=ConveyorDirection.LEFT,
                b_2_3=ConveyorDirection.RIGHT,
                b_4=ConveyorDirection.LEFT,
            ),
        )

    def test_low_goal_scoring_route(self):
        self.assertEqual(
            route_ball_in_scoring_mode(ScoreTarget.LOW),
            StorageRouting(
                f_1_2=ConveyorDirection.LEFT,
                f_3=ConveyorDirection.STOP,
                f_4=ConveyorDirection.STOP,
                b_1=ConveyorDirection.RIGHT,
                b_2_3=ConveyorDirection.RIGHT,
                b_4=ConveyorDirection.RIGHT,
            ),
        )

    def test_middle_goal_scoring_route(self):
        self.assertEqual(
            route_ball_in_scoring_mode(ScoreTarget.MIDDLE),
            StorageRouting(
                f_1_2=ConveyorDirection.RIGHT,
                f_3=ConveyorDirection.LEFT,
                f_4=ConveyorDirection.STOP,
                b_1=ConveyorDirection.RIGHT,
                b_2_3=ConveyorDirection.RIGHT,
                b_4=ConveyorDirection.RIGHT,
            ),
        )

    def test_high_goal_scoring_route(self):
        self.assertEqual(
            route_ball_in_scoring_mode(ScoreTarget.HIGH),
            StorageRouting(
                f_1_2=ConveyorDirection.RIGHT,
                f_3=ConveyorDirection.RIGHT,
                f_4=ConveyorDirection.LEFT,
                b_1=ConveyorDirection.RIGHT,
                b_2_3=ConveyorDirection.RIGHT,
                b_4=ConveyorDirection.RIGHT,
            ),
        )

    def test_opponent_ball_routes_into_overhead_hold(self):
        routing = route_ball_in_storage_mode(BallColor.BLUE, alliance_color=BallColor.RED)

        self.assertEqual(
            routing,
            StorageRouting(
                f_1_2=ConveyorDirection.RIGHT,
                f_3=ConveyorDirection.RIGHT,
                f_4=ConveyorDirection.RIGHT,
                b_1=ConveyorDirection.LEFT,
                b_2_3=ConveyorDirection.RIGHT,
                b_4=ConveyorDirection.RIGHT,
            ),
        )


if __name__ == "__main__":
    unittest.main()
