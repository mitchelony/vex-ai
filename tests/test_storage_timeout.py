import unittest

from vexai.storage_timeout import diverter_should_spin


class StorageTimeoutTests(unittest.TestCase):
    def test_diverter_spins_when_valid_color_was_seen_recently(self):
        self.assertTrue(
            diverter_should_spin(
                route="alliance",
                now_ms=7000,
                last_valid_color_seen_ms=2500,
                timeout_ms=5000,
            )
        )

    def test_diverter_stops_after_timeout_without_new_valid_color(self):
        self.assertFalse(
            diverter_should_spin(
                route="opponent",
                now_ms=9001,
                last_valid_color_seen_ms=4000,
                timeout_ms=5000,
            )
        )

    def test_diverter_stops_when_no_valid_color_has_ever_been_seen(self):
        self.assertFalse(
            diverter_should_spin(
                route="unknown",
                now_ms=1000,
                last_valid_color_seen_ms=None,
                timeout_ms=5000,
            )
        )


if __name__ == "__main__":
    unittest.main()
