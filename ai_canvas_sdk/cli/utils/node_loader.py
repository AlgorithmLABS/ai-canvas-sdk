"""노드 파일에서 CustomNode 서브클래스를 동적으로 로드하는 모듈."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_canvas_sdk.custom_node import CustomNode


class NodeLoadError(Exception):
    """노드 로드 중 발생하는 예외."""

    pass


def load_node_class(
    file_path: str,
    class_name: str | None = None,
) -> type[CustomNode]:
    """
    노드 파일에서 CustomNode 서브클래스를 로드합니다.

    Args:
        file_path: 노드 파일 경로 (예: hello_node.py)
        class_name: 특정 클래스 이름 (None이면 자동 탐색)

    Returns:
        CustomNode 서브클래스

    Raises:
        NodeLoadError: 노드를 찾을 수 없는 경우
    """
    from ai_canvas_sdk.custom_node import CustomNode

    path = Path(file_path).resolve()

    if not path.exists():
        raise NodeLoadError(f"파일을 찾을 수 없습니다: {file_path}")

    if not path.suffix == ".py":
        raise NodeLoadError(f"Python 파일이 아닙니다: {file_path}")

    # 모듈 이름 생성
    module_name = f"_loaded_node_{path.stem}"

    # 모듈 스펙 생성
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise NodeLoadError(f"모듈을 로드할 수 없습니다: {file_path}")

    # 모듈 생성 및 로드
    module = importlib.util.module_from_spec(spec)

    # sys.path에 파일의 디렉토리 추가 (상대 import 지원)
    parent_dir = str(path.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise NodeLoadError(f"모듈 실행 중 오류 발생: {e}") from e

    # CustomNode 서브클래스 탐색
    node_classes: list[type[CustomNode]] = []

    for name, obj in inspect.getmembers(module, inspect.isclass):
        # CustomNode 자체는 제외하고, 서브클래스만 포함
        if issubclass(obj, CustomNode) and obj is not CustomNode:
            # 해당 모듈에서 정의된 클래스만 포함 (import한 클래스 제외)
            if obj.__module__ == module_name:
                node_classes.append(obj)

    if not node_classes:
        raise NodeLoadError(
            f"CustomNode 서브클래스를 찾을 수 없습니다: {file_path}\n"
            "CustomNode를 상속받는 클래스를 정의했는지 확인하세요."
        )

    # 특정 클래스 이름이 지정된 경우
    if class_name:
        for cls in node_classes:
            if cls.__name__ == class_name:
                return cls
        available = ", ".join(cls.__name__ for cls in node_classes)
        raise NodeLoadError(f"클래스 '{class_name}'을 찾을 수 없습니다.\n사용 가능한 클래스: {available}")

    # 클래스가 여러 개인 경우 경고
    if len(node_classes) > 1:
        available = ", ".join(cls.__name__ for cls in node_classes)
        print(
            f"[WARNING] 여러 개의 노드 클래스가 발견되었습니다: {available}\n"
            f"첫 번째 클래스 '{node_classes[0].__name__}'을 사용합니다.\n"
            f"특정 클래스를 지정하려면 --class 옵션을 사용하세요."
        )

    return node_classes[0]


def list_node_classes(file_path: str) -> list[str]:
    """
    노드 파일에서 모든 CustomNode 서브클래스 이름을 반환합니다.

    Args:
        file_path: 노드 파일 경로

    Returns:
        클래스 이름 목록
    """
    from ai_canvas_sdk.custom_node import CustomNode

    path = Path(file_path).resolve()

    if not path.exists() or not path.suffix == ".py":
        return []

    module_name = f"_loaded_node_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        return []

    module = importlib.util.module_from_spec(spec)

    parent_dir = str(path.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    try:
        spec.loader.exec_module(module)
    except Exception:
        return []

    result = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, CustomNode) and obj is not CustomNode:
            if obj.__module__ == module_name:
                result.append(name)

    return result
