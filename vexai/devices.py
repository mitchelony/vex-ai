from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional


class DeviceType(Enum):
    DRIVE_MOTOR = auto()
    INTAKE_MOTOR = auto()
    AI_SENSOR = auto()
    OPTICAL_SENSOR = auto()
    GPS_SENSOR = auto()


class DeviceName(Enum):
    FRONT_LEFT = auto()
    FRONT_RIGHT = auto()
    BACK_LEFT = auto()
    BACK_RIGHT = auto()
    F_1_2 = auto()
    F_3 = auto()
    B_1 = auto()
    B_2_3 = auto()
    B_4 = auto()
    AI_VISION = auto()
    OPTICAL = auto()
    GPS = auto()


@dataclass(frozen=True)
class DevicePort:
    name: DeviceName
    label: str
    port: int
    device_type: DeviceType
    gear_ratio: Optional[str] = None


THOR_PORT_MAP: Dict[DeviceName, DevicePort] = {
    DeviceName.FRONT_LEFT: DevicePort(DeviceName.FRONT_LEFT, "front_left", 1, DeviceType.DRIVE_MOTOR, "ratio36_1"),
    DeviceName.FRONT_RIGHT: DevicePort(DeviceName.FRONT_RIGHT, "front_right", 2, DeviceType.DRIVE_MOTOR, "ratio36_1"),
    DeviceName.BACK_LEFT: DevicePort(DeviceName.BACK_LEFT, "back_left", 3, DeviceType.DRIVE_MOTOR, "ratio36_1"),
    DeviceName.BACK_RIGHT: DevicePort(DeviceName.BACK_RIGHT, "back_right", 4, DeviceType.DRIVE_MOTOR, "ratio36_1"),
    DeviceName.F_1_2: DevicePort(DeviceName.F_1_2, "f_1_2", 5, DeviceType.INTAKE_MOTOR, "ratio36_1"),
    DeviceName.F_3: DevicePort(DeviceName.F_3, "f_3", 6, DeviceType.INTAKE_MOTOR, "ratio36_1"),
    DeviceName.B_1: DevicePort(DeviceName.B_1, "b_1", 7, DeviceType.INTAKE_MOTOR, "ratio36_1"),
    DeviceName.B_2_3: DevicePort(DeviceName.B_2_3, "b_2_3", 8, DeviceType.INTAKE_MOTOR, "ratio36_1"),
    DeviceName.B_4: DevicePort(DeviceName.B_4, "b_4", 9, DeviceType.INTAKE_MOTOR, "ratio36_1"),
    DeviceName.AI_VISION: DevicePort(DeviceName.AI_VISION, "ai_vision_11", 11, DeviceType.AI_SENSOR),
    DeviceName.OPTICAL: DevicePort(DeviceName.OPTICAL, "optical_12", 12, DeviceType.OPTICAL_SENSOR),
    DeviceName.GPS: DevicePort(DeviceName.GPS, "gps_13", 13, DeviceType.GPS_SENSOR),
}


def get_devices_by_type(device_type: DeviceType) -> Dict[DeviceName, DevicePort]:
    return {
        name: device
        for name, device in THOR_PORT_MAP.items()
        if device.device_type == device_type
    }
