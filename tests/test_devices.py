import unittest

from vexai.devices import (
    DeviceName,
    DeviceType,
    THOR_PORT_MAP,
    get_devices_by_type,
)


class DeviceMapTests(unittest.TestCase):
    def test_thor_drive_ports_match_declared_layout(self):
        drive = get_devices_by_type(DeviceType.DRIVE_MOTOR)

        self.assertEqual(drive[DeviceName.FRONT_LEFT].port, 1)
        self.assertEqual(drive[DeviceName.FRONT_RIGHT].port, 2)
        self.assertEqual(drive[DeviceName.BACK_LEFT].port, 3)
        self.assertEqual(drive[DeviceName.BACK_RIGHT].port, 4)

    def test_thor_intake_ports_match_declared_layout(self):
        intake = get_devices_by_type(DeviceType.INTAKE_MOTOR)

        self.assertEqual(intake[DeviceName.F_1_2].port, 5)
        self.assertEqual(intake[DeviceName.F_3].port, 6)
        self.assertEqual(intake[DeviceName.B_1].port, 7)
        self.assertEqual(intake[DeviceName.B_2_3].port, 8)
        self.assertEqual(intake[DeviceName.B_4].port, 9)

    def test_thor_sensor_ports_match_declared_layout(self):
        self.assertEqual(THOR_PORT_MAP[DeviceName.AI_VISION].device_type, DeviceType.AI_SENSOR)
        self.assertEqual(THOR_PORT_MAP[DeviceName.AI_VISION].port, 11)

        self.assertEqual(THOR_PORT_MAP[DeviceName.OPTICAL].device_type, DeviceType.OPTICAL_SENSOR)
        self.assertEqual(THOR_PORT_MAP[DeviceName.OPTICAL].port, 12)

        self.assertEqual(THOR_PORT_MAP[DeviceName.GPS].device_type, DeviceType.GPS_SENSOR)
        self.assertEqual(THOR_PORT_MAP[DeviceName.GPS].port, 13)

    def test_all_declared_motors_use_same_gear_ratio(self):
        for device in THOR_PORT_MAP.values():
            if device.device_type in {DeviceType.DRIVE_MOTOR, DeviceType.INTAKE_MOTOR}:
                self.assertEqual(device.gear_ratio, "ratio36_1")


if __name__ == "__main__":
    unittest.main()
