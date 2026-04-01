from dataclasses import dataclass
from enum import Enum, auto


class BallColor(Enum):
    RED = auto()
    BLUE = auto()
    UNKNOWN = auto()


class ConveyorDirection(Enum):
    LEFT = auto()
    RIGHT = auto()
    STOP = auto()


class ThorMode(Enum):
    IDLE = auto()
    STORAGE = auto()
    SCORING = auto()


class ScoreTarget(Enum):
    LOW = auto()
    MIDDLE = auto()
    HIGH = auto()


@dataclass(frozen=True)
class StorageRouting:
    f_1_2: ConveyorDirection
    f_3: ConveyorDirection
    f_4: ConveyorDirection
    b_1: ConveyorDirection
    b_2_3: ConveyorDirection
    b_4: ConveyorDirection


def route_ball_in_storage_mode(detected_color: BallColor, alliance_color: BallColor) -> StorageRouting:
    diverter = ConveyorDirection.LEFT if detected_color == alliance_color else ConveyorDirection.RIGHT

    return StorageRouting(
        f_1_2=ConveyorDirection.RIGHT,
        f_3=ConveyorDirection.RIGHT,
        f_4=ConveyorDirection.LEFT if detected_color == alliance_color else ConveyorDirection.RIGHT,
        b_1=ConveyorDirection.LEFT,
        b_2_3=ConveyorDirection.RIGHT,
        b_4=diverter,
    )


def route_ball_in_scoring_mode(target: ScoreTarget) -> StorageRouting:
    if target == ScoreTarget.LOW:
        return StorageRouting(
            f_1_2=ConveyorDirection.LEFT,
            f_3=ConveyorDirection.STOP,
            f_4=ConveyorDirection.STOP,
            b_1=ConveyorDirection.RIGHT,
            b_2_3=ConveyorDirection.RIGHT,
            b_4=ConveyorDirection.RIGHT,
        )

    if target == ScoreTarget.MIDDLE:
        return StorageRouting(
            f_1_2=ConveyorDirection.RIGHT,
            f_3=ConveyorDirection.LEFT,
            f_4=ConveyorDirection.STOP,
            b_1=ConveyorDirection.RIGHT,
            b_2_3=ConveyorDirection.RIGHT,
            b_4=ConveyorDirection.RIGHT,
        )

    return StorageRouting(
        f_1_2=ConveyorDirection.RIGHT,
        f_3=ConveyorDirection.RIGHT,
        f_4=ConveyorDirection.LEFT,
        b_1=ConveyorDirection.RIGHT,
        b_2_3=ConveyorDirection.RIGHT,
        b_4=ConveyorDirection.RIGHT,
    )
