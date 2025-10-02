from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValueTypeEnum(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    STRING_ARRAY = "stringArray"
    NUMBER_ARRAY = "numberArray"
    OBJECT_ARRAY = "objectArray"
    UNKNOWN = "unknown"


@dataclass
class Parameter:
    text: str
    name: str
    form_type: str
    value: Any | None = None
    value_type: ValueTypeEnum = ValueTypeEnum.STRING
    mode: dict | None = None
    options: dict | None = None
    is_tab: bool | None = None
