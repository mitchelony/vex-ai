from enum import Enum, auto
from typing import Tuple


class BenchMode(Enum):
    IDLE = auto()
    STORAGE = auto()
    SCORING = auto()


class BenchGoalTarget(Enum):
    LOW = auto()
    MIDDLE = auto()
    HIGH = auto()


def _clamp_percent(value: int) -> int:
    return max(-100, min(100, value))


def mix_arcade_drive(forward_pct: int, turn_pct: int) -> Tuple[int, int]:
    left_speed = _clamp_percent(forward_pct + turn_pct)
    right_speed = _clamp_percent(forward_pct - turn_pct)
    return left_speed, right_speed


def active_mode_from_triggers(*, r1_pressed: bool, r2_pressed: bool) -> BenchMode:
    if r2_pressed:
        return BenchMode.SCORING
    if r1_pressed:
        return BenchMode.STORAGE
    return BenchMode.IDLE


def selected_goal_target(
    current_target: BenchGoalTarget,
    *,
    up_pressed: bool,
    left_pressed: bool,
    down_pressed: bool,
) -> BenchGoalTarget:
    if up_pressed:
        return BenchGoalTarget.HIGH
    if left_pressed:
        return BenchGoalTarget.MIDDLE
    if down_pressed:
        return BenchGoalTarget.LOW
    return current_target


def selected_alliance_color(current_color: str, *, a_pressed: bool, b_pressed: bool) -> str:
    if b_pressed:
        return "red"
    if a_pressed:
        return "blue"
    return current_color
