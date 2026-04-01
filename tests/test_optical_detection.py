import unittest

from vexai.optical_detection import classify_ball_color


class OpticalDetectionTests(unittest.TestCase):
    def test_returns_unknown_when_no_object_is_near(self):
        self.assertEqual(
            classify_ball_color(hue_degrees=5, brightness_pct=80, is_near_object=False),
            "unknown",
        )

    def test_returns_unknown_when_object_is_too_dark(self):
        self.assertEqual(
            classify_ball_color(hue_degrees=220, brightness_pct=3, is_near_object=True),
            "unknown",
        )

    def test_classifies_blue_from_hue_range(self):
        self.assertEqual(
            classify_ball_color(hue_degrees=220, brightness_pct=40, is_near_object=True),
            "blue",
        )

    def test_classifies_red_from_low_hue_range(self):
        self.assertEqual(
            classify_ball_color(hue_degrees=10, brightness_pct=40, is_near_object=True),
            "red",
        )

    def test_classifies_red_from_wrapped_hue_range(self):
        self.assertEqual(
            classify_ball_color(hue_degrees=350, brightness_pct=40, is_near_object=True),
            "red",
        )

    def test_returns_unknown_for_hues_outside_supported_ball_ranges(self):
        self.assertEqual(
            classify_ball_color(hue_degrees=120, brightness_pct=40, is_near_object=True),
            "unknown",
        )


if __name__ == "__main__":
    unittest.main()
