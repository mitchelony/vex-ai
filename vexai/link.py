from vexai.robots import RobotName
from vexai.state import FieldRegion, LoadState, PartnerTelemetry


PROTOCOL_VERSION = "1"


def encode_packet(telemetry: PartnerTelemetry) -> str:
    health_flags = ",".join(telemetry.health_flags)
    return "|".join(
        [
            PROTOCOL_VERSION,
            telemetry.robot.name.lower(),
            str(int(telemetry.timestamp_ms)),
            str(float(telemetry.x_mm)),
            str(float(telemetry.y_mm)),
            str(float(telemetry.heading_deg)),
            telemetry.load_state.value,
            telemetry.intent_kind or "",
            telemetry.target_region.value,
            health_flags,
        ]
    )


def decode_packet(packet: str) -> PartnerTelemetry:
    parts = packet.strip().split("|")
    if len(parts) != 10:
        raise ValueError("Expected 10 packet fields, got %s" % len(parts))
    version = parts[0]
    if version != PROTOCOL_VERSION:
        raise ValueError("Unsupported packet version: %s" % version)
    health_flags = tuple(flag for flag in parts[9].split(",") if flag)
    return PartnerTelemetry(
        robot=RobotName[parts[1].upper()],
        timestamp_ms=int(parts[2]),
        x_mm=float(parts[3]),
        y_mm=float(parts[4]),
        heading_deg=float(parts[5]),
        load_state=LoadState(parts[6]),
        intent_kind=parts[7] or None,
        target_region=FieldRegion(parts[8]),
        health_flags=health_flags,
    )
