MIN_BALL_BRIGHTNESS_PCT = 8
RED_HUE_MAX = 25
RED_HUE_WRAP_MIN = 330
BLUE_HUE_MIN = 180
BLUE_HUE_MAX = 260


def classify_ball_color(*, hue_degrees: float, brightness_pct: float, is_near_object: bool) -> str:
    if not is_near_object:
        return "unknown"

    if brightness_pct < MIN_BALL_BRIGHTNESS_PCT:
        return "unknown"

    if RED_HUE_WRAP_MIN <= hue_degrees <= 360 or 0 <= hue_degrees <= RED_HUE_MAX:
        return "red"

    if BLUE_HUE_MIN <= hue_degrees <= BLUE_HUE_MAX:
        return "blue"

    return "unknown"
