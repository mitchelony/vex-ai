import unittest

from vexai.storage_memory import latched_storage_route


class StorageMemoryTests(unittest.TestCase):
    def test_updates_to_alliance_route_when_detected_color_matches_alliance(self):
        self.assertEqual(
            latched_storage_route(
                previous_route="opponent",
                detected_color="blue",
                alliance_color="blue",
            ),
            "alliance",
        )

    def test_updates_to_opponent_route_when_detected_color_differs_from_alliance(self):
        self.assertEqual(
            latched_storage_route(
                previous_route="alliance",
                detected_color="red",
                alliance_color="blue",
            ),
            "opponent",
        )

    def test_keeps_previous_route_when_color_is_unknown(self):
        self.assertEqual(
            latched_storage_route(
                previous_route="opponent",
                detected_color="unknown",
                alliance_color="blue",
            ),
            "opponent",
        )


if __name__ == "__main__":
    unittest.main()
