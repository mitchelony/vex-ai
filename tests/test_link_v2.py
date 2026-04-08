import unittest

from vexai.link import decode_packet, encode_packet
from vexai.planner import IntentKind
from vexai.robots import RobotName
from vexai.state import FieldRegion, LoadState, PartnerTelemetry


class LinkPacketTests(unittest.TestCase):
    def test_encode_decode_round_trip_preserves_fields(self):
        telemetry = PartnerTelemetry(
            robot=RobotName.THOR,
            timestamp_ms=1_250,
            x_mm=120.0,
            y_mm=-45.0,
            heading_deg=91.0,
            load_state=LoadState.ALLIANCE_HELD,
            intent_kind=IntentKind.COLLECT_REGION.value,
            target_region=FieldRegion.CENTER_GOAL,
            health_flags=("gps_ok", "vision_ok"),
        )

        decoded = decode_packet(encode_packet(telemetry))

        self.assertEqual(decoded.robot, telemetry.robot)
        self.assertEqual(decoded.timestamp_ms, telemetry.timestamp_ms)
        self.assertEqual(decoded.load_state, telemetry.load_state)
        self.assertEqual(decoded.target_region, telemetry.target_region)
        self.assertEqual(decoded.health_flags, telemetry.health_flags)


if __name__ == "__main__":
    unittest.main()
