"""SDK 테스트 공용 설정.

슬림 테스트 환경(pandas/pyarrow/grpc 미설치)에서도 ``ai_canvas_sdk`` 패키지를 import 할 수
있도록, 무거운 leaf 모듈(serialization=pandas, grpc=protobuf)을 **미설치일 때만** stub 한다.
full-deps 환경(SDK CI)에서는 실제 모듈이 import 되므로 stub 이 끼어들지 않는다.
custom_node(순수 dataclass) / cli 는 항상 실제 코드가 로드된다.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from unittest.mock import MagicMock


def _missing(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is None
    except (ImportError, ModuleNotFoundError, ValueError):
        return True


# serialization.py 는 pandas/pyarrow + 생성된 protobuf 를 module-top import 한다. pandas/pyarrow 가
# 없을 때만 stub 하여 `import ai_canvas_sdk` (→ DataSerializer) 를 가능케 한다. grpc/protobuf 자체는
# stub 하지 않는다 — proto 의존 테스트는 실제 grpc 런타임이 필요하며, 없으면 해당 테스트만 명시적으로
# 실패하도록 둔다(가짜 통과 방지). full-deps CI 에서는 둘 다 설치되어 stub 이 끼어들지 않는다.
if _missing("pandas") or _missing("pyarrow"):
    _ser = types.ModuleType("ai_canvas_sdk.serialization")
    _ser.DataSerializer = MagicMock()
    sys.modules.setdefault("ai_canvas_sdk.serialization", _ser)

