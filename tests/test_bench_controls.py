import unittest

from vexai.bench_controls import (
    BenchGoalTarget,
    BenchMode,
    active_mode_from_triggers,
    mix_arcade_drive,
    selected_goal_target,
    selected_alliance_color,
)


class BenchControlsTests(unittest.TestCase):
    def test_r1_selects_storage_mode(self):
        self.assertEqual(
            active_mode_from_triggers(
                r1_pressed=True,
                r2_pressed=False,
            ),
            BenchMode.STORAGE,
        )

    def test_r2_selects_scoring_mode(self):
        self.assertEqual(
            active_mode_from_triggers(
                r1_pressed=False,
                r2_pressed=True,
            ),
            BenchMode.SCORING,
        )

    def test_no_trigger_returns_idle_mode(self):
        self.assertEqual(
            active_mode_from_triggers(
                r1_pressed=False,
                r2_pressed=False,
            ),
            BenchMode.IDLE,
        )

    def test_r2_wins_when_both_mode_triggers_are_pressed(self):
        self.assertEqual(
            active_mode_from_triggers(
                r1_pressed=True,
                r2_pressed=True,
            ),
            BenchMode.SCORING,
        )

    def test_down_selects_low_goal_target(self):
        self.assertEqual(
            selected_goal_target(
                BenchGoalTarget.HIGH,
                up_pressed=False,
                left_pressed=False,
                down_pressed=True,
            ),
            BenchGoalTarget.LOW,
        )

    def test_left_selects_middle_goal_target(self):
        self.assertEqual(
            selected_goal_target(
                BenchGoalTarget.LOW,
                up_pressed=False,
                left_pressed=True,
                down_pressed=False,
            ),
            BenchGoalTarget.MIDDLE,
        )

    def test_up_selects_high_goal_target(self):
        self.assertEqual(
            selected_goal_target(
                BenchGoalTarget.LOW,
                up_pressed=True,
                left_pressed=False,
                down_pressed=False,
            ),
            BenchGoalTarget.HIGH,
        )

    def test_alliance_color_buttons_switch_between_blue_and_red(self):
        color = selected_alliance_color("blue", a_pressed=False, b_pressed=True)
        self.assertEqual(color, "red")

        color = selected_alliance_color(color, a_pressed=True, b_pressed=False)
        self.assertEqual(color, "blue")

    def test_arcade_drive_mixes_forward_and_turn(self):
        self.assertEqual(mix_arcade_drive(50, 10), (60, 40))

    def test_arcade_drive_clamps_to_v5_percent_range(self):
        self.assertEqual(mix_arcade_drive(90, 30), (100, 60))
        self.assertEqual(mix_arcade_drive(-90, -30), (-100, -60))


if __name__ == "__main__":
    unittest.main()
