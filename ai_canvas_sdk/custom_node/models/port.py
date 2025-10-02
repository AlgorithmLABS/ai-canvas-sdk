from dataclasses import dataclass
from enum import Enum


class PortEnum(Enum):
    """포트 타입"""

    SOURCE = "source"
    TARGET = "target"


class PositionEnum(Enum):
    """포트 위치"""

    RIGHT = "right"
    LEFT = "left"
    TOP = "top"
    BOTTOM = "bottom"


class PortTypeEnum(Enum):
    """포트 타입"""

    DATASET = "dataset"
    UNTRAINED = "untrainedModel"
    TRAINED = "trainedModel"
    TRANSFORMER = "transformer"
    DISPLAY = "display"


@dataclass
class Port:
    """포트 정의"""

    type: PortEnum
    position: PositionEnum
    port_type: PortTypeEnum
    label: str | None = None
    required: bool = True
