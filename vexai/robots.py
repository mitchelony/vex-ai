from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List


class RobotName(Enum):
    THOR = auto()
    LOKI = auto()


class IntakeStyle(Enum):
    VERTICAL = auto()
    INCLINE = auto()


class BallRoute(Enum):
    TO_ALLIANCE_STORAGE = auto()
    TO_OPPONENT_HOLD = auto()
    DIRECT_SCORE_ONLY = auto()


class GoalHeight(Enum):
    LOW = auto()
    HIGH = auto()


class ThorMode(Enum):
    STORAGE = auto()
    SCORING = auto()


@dataclass(frozen=True)
class SensorSuite:
    ai_front: bool
    gps_present: bool
    optical_in_intake: bool


@dataclass(frozen=True)
class RobotProfile:
    name: RobotName
    role_summary: str
    intake_style: IntakeStyle
    has_storage: bool
    sensor_suite: SensorSuite
    scoring_heights: List[GoalHeight]
    supported_modes: List[ThorMode]
    ball_routes: Dict[str, BallRoute]


THOR_PROFILE = RobotProfile(
    name=RobotName.THOR,
    role_summary="Primary storage and scoring bot with alliance-ball sort and opponent-ball denial.",
    intake_style=IntakeStyle.VERTICAL,
    has_storage=True,
    sensor_suite=SensorSuite(ai_front=True, gps_present=True, optical_in_intake=True),
    scoring_heights=[GoalHeight.LOW, GoalHeight.HIGH],
    supported_modes=[ThorMode.STORAGE, ThorMode.SCORING],
    ball_routes={
        "alliance_intake": BallRoute.TO_ALLIANCE_STORAGE,
        "opponent_intake": BallRoute.TO_OPPONENT_HOLD,
    },
)

LOKI_PROFILE = RobotProfile(
    name=RobotName.LOKI,
    role_summary="Fast direct-intake scorer for low and high goals with no ball storage.",
    intake_style=IntakeStyle.INCLINE,
    has_storage=False,
    sensor_suite=SensorSuite(ai_front=True, gps_present=True, optical_in_intake=True),
    scoring_heights=[GoalHeight.LOW, GoalHeight.HIGH],
    supported_modes=[],
    ball_routes={
        "direct_score": BallRoute.DIRECT_SCORE_ONLY,
    },
)


def get_robot_profile(name: RobotName) -> RobotProfile:
    if name == RobotName.THOR:
        return THOR_PROFILE
    if name == RobotName.LOKI:
        return LOKI_PROFILE
    raise ValueError(f"Unsupported robot name: {name}")
