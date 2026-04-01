#region VEXcode Generated Robot Configuration
from vex import *
import urandom
import math

# Brain should be defined by default
brain=Brain()

# Robot configuration code
# AI Classification Competition Element IDs - Push Back
class GameElementsPushBack:
    BLUE_BLOCK = 0
    RED_BLOCK = 1
controller_1 = Controller(PRIMARY)
# AI Vision Color Descriptions
# AI Vision Code Descriptions
ai_vision_11 = AiVision(Ports.PORT11, AiVision.ALL_AIOBJS)
optical_12 = Optical(Ports.PORT12)
gps_13 = Gps(Ports.PORT13, 0.00, -587.38, MM, 180)
f_1_2 = Motor(Ports.PORT5, GearSetting.RATIO_36_1, False)
f_3 = Motor(Ports.PORT6, GearSetting.RATIO_36_1, False)
b_1 = Motor(Ports.PORT7, GearSetting.RATIO_36_1, False)
b_2_3 = Motor(Ports.PORT8, GearSetting.RATIO_36_1, False)
b_4 = Motor(Ports.PORT9, GearSetting.RATIO_36_1, False)
f_4 = Motor(Ports.PORT20, GearSetting.RATIO_36_1, False)
left_motor_a = Motor(Ports.PORT1, GearSetting.RATIO_36_1, False)
left_motor_b = Motor(Ports.PORT2, GearSetting.RATIO_36_1, False)
left_drive_smart = MotorGroup(left_motor_a, left_motor_b)
right_motor_a = Motor(Ports.PORT3, GearSetting.RATIO_36_1, True)
right_motor_b = Motor(Ports.PORT4, GearSetting.RATIO_36_1, True)
right_drive_smart = MotorGroup(right_motor_a, right_motor_b)
drivetrain_gps = Gps(Ports.PORT19, 0.00, -587.38, MM, 180)
drivetrain = SmartDrive(left_drive_smart, right_drive_smart, drivetrain_gps, 319.19, 320, 40, MM, 1)


# wait for rotation sensor to fully initialize
wait(30, MSEC)


# Make random actually random
def initializeRandomSeed():
    wait(100, MSEC)
    random = brain.battery.voltage(MV) + brain.battery.current(CurrentUnits.AMP) * 100 + brain.timer.system_high_res()
    urandom.seed(int(random))
      
# Set random seed 
initializeRandomSeed()

vexcode_initial_drivetrain_calibration_completed = False
def calibrate_drivetrain():
    # Calibrate the Drivetrain GPS
    global vexcode_initial_drivetrain_calibration_completed
    sleep(200, MSEC)
    brain.screen.print("Calibrating")
    brain.screen.next_row()
    brain.screen.print("GPS")
    drivetrain_gps.calibrate()
    while drivetrain_gps.is_calibrating():
        sleep(25, MSEC)
    vexcode_initial_drivetrain_calibration_completed = True
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)


# Calibrate the Drivetrain
calibrate_drivetrain()


# Color to String Helper
def convert_color_to_string(col):
    if col == Color.RED:
        return "red"
    if col == Color.GREEN:
        return "green"
    if col == Color.BLUE:
        return "blue"
    if col == Color.WHITE:
        return "white"
    if col == Color.YELLOW:
        return "yellow"
    if col == Color.ORANGE:
        return "orange"
    if col == Color.PURPLE:
        return "purple"
    if col == Color.CYAN:
        return "cyan"
    if col == Color.BLACK:
        return "black"
    if col == Color.TRANSPARENT:
        return "transparent"
    return ""

def play_vexcode_sound(sound_name):
    # Helper to make playing sounds from the V5 in VEXcode easier and
    # keeps the code cleaner by making it clear what is happening.
    print("VEXPlaySound:" + sound_name)
    wait(5, MSEC)

# add a small delay to make sure we don't print in the middle of the REPL header
wait(200, MSEC)
# clear the console to make sure we don't have the REPL in the console
print("\033[2J")

#endregion VEXcode Generated Robot Configuration

# ------------------------------------------
# 
# 	Project:      VEXcode Project
#	Author:       VEX
#	Created:
#	Description:  VEXcode V5 Python Project 
# 
# ------------------------------------------

# Library imports
from vex import *

# Begin project code

ALLIANCE_COLOR = "blue"
LEFT_SPIN = REVERSE
RIGHT_SPIN = FORWARD
INTAKE_SPEED_PCT = 80
DIVERTER_SPEED_PCT = 65
OPPONENT_LAUNCH_SPEED_PCT = 90
SCORING_SPEED_PCT = 80
DRIVE_DEADBAND_PCT = 5
SCORE_TARGET = "low"
STORAGE_ROUTE = "unknown"
LAST_VALID_COLOR_SEEN_MS = None
STORAGE_ROUTE_TIMEOUT_MS = 5000
MIN_BALL_BRIGHTNESS_PCT = 8
RED_HUE_MAX = 25
RED_HUE_WRAP_MIN = 330
BLUE_HUE_MIN = 180
BLUE_HUE_MAX = 260


def set_alliance_color(color_name):
    global ALLIANCE_COLOR
    ALLIANCE_COLOR = color_name


def spin_left(motor, speed_pct):
    motor.spin(LEFT_SPIN, speed_pct, PERCENT)


def spin_right(motor, speed_pct):
    motor.spin(RIGHT_SPIN, speed_pct, PERCENT)


def clamp_percent(speed_pct):
    return max(-100, min(100, int(speed_pct)))


def spin_drive_group(motor_group, speed_pct):
    speed_pct = clamp_percent(speed_pct)
    if abs(speed_pct) <= DRIVE_DEADBAND_PCT:
        motor_group.stop()
        return

    direction = FORWARD if speed_pct >= 0 else REVERSE
    motor_group.spin(direction, abs(speed_pct), PERCENT)


def run_arcade_drive():
    forward = controller_1.axis3.position()
    turn = controller_1.axis4.position()
    left_speed = clamp_percent(forward + turn)
    right_speed = clamp_percent(forward - turn)

    spin_drive_group(left_drive_smart, left_speed)
    spin_drive_group(right_drive_smart, right_speed)


def stop_storage_path():
    f_1_2.stop()
    f_3.stop()
    f_4.stop()
    b_1.stop()
    b_2_3.stop()
    b_4.stop()


def classify_ball_color_from_optical(hue_degrees, brightness_pct, is_near_object):
    if not is_near_object:
        return "unknown"

    if brightness_pct < MIN_BALL_BRIGHTNESS_PCT:
        return "unknown"

    if RED_HUE_WRAP_MIN <= hue_degrees <= 360 or 0 <= hue_degrees <= RED_HUE_MAX:
        return "red"

    if BLUE_HUE_MIN <= hue_degrees <= BLUE_HUE_MAX:
        return "blue"

    return "unknown"


def get_optical_snapshot():
    hue = optical_12.hue()
    brightness = optical_12.brightness()
    is_near_object = optical_12.is_near_object()
    detected_color = classify_ball_color_from_optical(hue, brightness, is_near_object)
    return detected_color, hue, brightness, is_near_object


def update_storage_route(previous_route, detected_color):
    if detected_color == "unknown":
        return previous_route
    if detected_color == ALLIANCE_COLOR:
        return "alliance"
    return "opponent"


def run_storage_mode():
    global STORAGE_ROUTE
    global LAST_VALID_COLOR_SEEN_MS
    detected_color, _, _, _ = get_optical_snapshot()
    STORAGE_ROUTE = update_storage_route(STORAGE_ROUTE, detected_color)
    now_ms = brain.timer.time(MSEC)
    if detected_color != "unknown":
        LAST_VALID_COLOR_SEEN_MS = now_ms

    spin_right(f_1_2, INTAKE_SPEED_PCT)
    spin_right(f_3, INTAKE_SPEED_PCT)

    spin_left(b_1, INTAKE_SPEED_PCT)
    spin_right(b_2_3, INTAKE_SPEED_PCT)

    if STORAGE_ROUTE == "alliance":
        spin_left(f_4, INTAKE_SPEED_PCT)
    else:
        spin_right(f_4, OPPONENT_LAUNCH_SPEED_PCT)

    if LAST_VALID_COLOR_SEEN_MS is not None and now_ms - LAST_VALID_COLOR_SEEN_MS <= STORAGE_ROUTE_TIMEOUT_MS:
        if STORAGE_ROUTE == "alliance":
            spin_left(b_4, DIVERTER_SPEED_PCT)
        elif STORAGE_ROUTE == "opponent":
            spin_right(b_4, OPPONENT_LAUNCH_SPEED_PCT)
        else:
            b_4.stop()
    else:
        b_4.stop()

    return detected_color


def run_scoring_mode():
    spin_right(b_1, SCORING_SPEED_PCT)
    spin_right(b_2_3, SCORING_SPEED_PCT)
    spin_right(b_4, SCORING_SPEED_PCT)

    if SCORE_TARGET == "low":
        spin_left(f_1_2, SCORING_SPEED_PCT)
        f_3.stop()
        f_4.stop()
    elif SCORE_TARGET == "middle":
        spin_right(f_1_2, SCORING_SPEED_PCT)
        spin_left(f_3, SCORING_SPEED_PCT)
        f_4.stop()
    else:
        spin_right(f_1_2, SCORING_SPEED_PCT)
        spin_right(f_3, SCORING_SPEED_PCT)
        spin_left(f_4, SCORING_SPEED_PCT)


def draw_status(active_mode, detected_color, hue_degrees, brightness_pct, is_near_object):
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("Thor Bench Test")
    brain.screen.new_line()
    brain.screen.print("Alliance: {}".format(ALLIANCE_COLOR))
    brain.screen.new_line()
    brain.screen.print("Mode: {}".format(active_mode))
    brain.screen.new_line()
    brain.screen.print("Target: {}".format(SCORE_TARGET))
    brain.screen.new_line()
    brain.screen.print("Ball: {}".format(detected_color))
    brain.screen.new_line()
    brain.screen.print("Hue:{:.0f} Bright:{:.0f}".format(hue_degrees, brightness_pct))
    brain.screen.new_line()
    brain.screen.print("Near: {}".format("yes" if is_near_object else "no"))
    brain.screen.new_line()
    brain.screen.print("Route: {}".format(STORAGE_ROUTE))
    brain.screen.new_line()
    if LAST_VALID_COLOR_SEEN_MS is None:
        brain.screen.print("B4: waiting")
    else:
        age_ms = int(brain.timer.time(MSEC) - LAST_VALID_COLOR_SEEN_MS)
        brain.screen.print("B4 age: {}ms".format(age_ms))
    brain.screen.new_line()
    brain.screen.print("R1 storage  R2 scoring")
    brain.screen.new_line()
    brain.screen.print("Up high  Left middle")
    brain.screen.new_line()
    brain.screen.print("Down low  A blue  B red")


def update_alliance_selection():
    global ALLIANCE_COLOR
    if controller_1.buttonA.pressing():
        ALLIANCE_COLOR = "blue"
    elif controller_1.buttonB.pressing():
        ALLIANCE_COLOR = "red"


def update_score_target():
    global SCORE_TARGET
    if controller_1.buttonUp.pressing():
        SCORE_TARGET = "high"
    elif controller_1.buttonLeft.pressing():
        SCORE_TARGET = "middle"
    elif controller_1.buttonDown.pressing():
        SCORE_TARGET = "low"


def main():
    detected_color = "unknown"
    hue_degrees = 0
    brightness_pct = 0
    is_near_object = False
    optical_12.set_light_power(100, PERCENT)

    while True:
        run_arcade_drive()
        update_alliance_selection()
        update_score_target()

        if controller_1.buttonR2.pressing():
            active_mode = "scoring"
            run_scoring_mode()
            detected_color, hue_degrees, brightness_pct, is_near_object = get_optical_snapshot()
        elif controller_1.buttonR1.pressing():
            active_mode = "storage"
            detected_color = run_storage_mode()
            _, hue_degrees, brightness_pct, is_near_object = get_optical_snapshot()
        else:
            active_mode = "idle"
            stop_storage_path()
            detected_color, hue_degrees, brightness_pct, is_near_object = get_optical_snapshot()

        draw_status(active_mode, detected_color, hue_degrees, brightness_pct, is_near_object)
        wait(20, MSEC)


main()
