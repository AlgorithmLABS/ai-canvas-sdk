"""커스텀 노드 테스트 커맨드 구현."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd


def _load_input_data(input_path: str, port_labels: list[str]) -> dict[str, Any]:
    """
    입력 데이터 파일을 로드합니다.

    Args:
        input_path: 입력 파일 경로 (JSON 또는 CSV)
        port_labels: 입력 포트 레이블 목록

    Returns:
        입력 데이터 딕셔너리 (포트 레이블 -> DataFrame)
    """
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

    suffix = path.suffix.lower()

    if suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # JSON 형식 1: {"port_label": [...]} - 포트별 데이터
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, list):
                    result[key] = pd.DataFrame(value)
                elif isinstance(value, dict):
                    # 단일 row를 list로 변환
                    result[key] = pd.DataFrame([value])
                else:
                    result[key] = value
            return result

        # JSON 형식 2: [...] - 단일 포트 데이터 (첫 번째 포트에 할당)
        if isinstance(data, list):
            if port_labels:
                return {port_labels[0]: pd.DataFrame(data)}
            return {"input": pd.DataFrame(data)}

    elif suffix == ".csv":
        df = pd.read_csv(path)
        # 단일 CSV는 첫 번째 입력 포트에 할당
        if port_labels:
            return {port_labels[0]: df}
        return {"input": df}

    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}\n지원 형식: .json, .csv")

    return {}


def _parse_params(params_str: str | None) -> dict[str, Any]:
    """파라미터 JSON 문자열을 파싱합니다."""
    if not params_str:
        return {}

    try:
        params = json.loads(params_str)
        if not isinstance(params, dict):
            raise ValueError("파라미터는 JSON 객체여야 합니다.")
        return params
    except json.JSONDecodeError as e:
        raise ValueError(f"파라미터 JSON 파싱 실패: {e}") from e


def _save_output(output_path: str, result: dict[str, Any]) -> None:
    """결과를 파일로 저장합니다."""
    path = Path(output_path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        # DataFrame을 dict로 변환
        serializable = {}
        for key, value in result.items():
            if isinstance(value, pd.DataFrame):
                serializable[key] = value.to_dict(orient="records")
            else:
                serializable[key] = value

        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2, default=str)

    elif suffix == ".csv":
        # 첫 번째 DataFrame만 저장
        for key, value in result.items():
            if isinstance(value, pd.DataFrame):
                value.to_csv(path, index=False, encoding="utf-8")
                break
        else:
            raise ValueError("저장할 DataFrame이 없습니다.")

    else:
        raise ValueError(f"지원하지 않는 출력 형식입니다: {suffix}\n지원 형식: .json, .csv")

    print(f"\n결과가 저장되었습니다: {path}")


def _print_result(result: dict[str, Any], max_rows: int = 10) -> None:
    """결과를 터미널에 출력합니다."""
    print("\n" + "=" * 50)
    print("Output")
    print("=" * 50)

    for port_label, data in result.items():
        print(f"\n[{port_label}]")

        if isinstance(data, pd.DataFrame):
            if len(data) > max_rows:
                print(f"(총 {len(data)}행 중 상위 {max_rows}행 표시)")
                print(data.head(max_rows).to_string())
            else:
                print(data.to_string())
        else:
            print(f"  {data}")


def run_test(args: argparse.Namespace) -> int:
    """테스트 커맨드 실행."""
    from ai_canvas_sdk.cli.utils.node_loader import NodeLoadError, load_node_class
    from ai_canvas_sdk.cli.utils.schema_validator import (
        format_validation_result,
        validate_schema,
    )
    from ai_canvas_sdk.cli.utils.test_context import create_test_context

    node_file = args.node_file
    class_name = getattr(args, "class", None) or getattr(args, "class_name", None)
    validate_only = getattr(args, "validate_only", False)
    input_file = getattr(args, "input", None)
    params_str = getattr(args, "params", None)
    output_file = getattr(args, "output", None)
    verbose = getattr(args, "verbose", False)

    # 1. 노드 클래스 로드
    print(f"Loading node from: {node_file}")
    print("-" * 50)

    try:
        node_class = load_node_class(node_file, class_name)
        print(f"Node class loaded: {node_class.__name__}")
    except NodeLoadError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        return 1

    # 2. 스키마 검증
    print("\nValidating schema...")
    validation_result = validate_schema(node_class)
    print(format_validation_result(validation_result, verbose=verbose))

    if not validation_result.is_valid:
        return 1

    # 3. --validate-only인 경우 여기서 종료
    if validate_only:
        return 0

    # 4. 노드 실행
    schema = validation_result.schema
    if schema is None:
        print("[ERROR] 스키마를 가져올 수 없습니다.", file=sys.stderr)
        return 1

    # 입력 포트 레이블 추출
    input_port_labels = [
        port.label or f"input_{i}"
        for i, port in enumerate(schema.data.input_ports or [])
    ]

    # 입력 데이터 로드
    if input_file:
        try:
            inputs = _load_input_data(input_file, input_port_labels)
            print(f"\nInput data loaded from: {input_file}")
            for label, data in inputs.items():
                if isinstance(data, pd.DataFrame):
                    print(f"  - {label}: {len(data)} rows, {len(data.columns)} columns")
        except (FileNotFoundError, ValueError) as e:
            print(f"\n[ERROR] {e}", file=sys.stderr)
            return 1
    else:
        # 입력 파일이 없으면 빈 DataFrame으로 시작
        inputs = {}
        for label in input_port_labels:
            inputs[label] = pd.DataFrame()
        if inputs:
            print("\n[INFO] 입력 파일이 지정되지 않았습니다. 빈 DataFrame을 사용합니다.")

    # 파라미터 파싱
    try:
        params = _parse_params(params_str)
    except ValueError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        return 1

    # 스키마에서 기본 파라미터 값 적용
    for param in schema.data.params or []:
        if param.name not in params and param.value is not None:
            params[param.name] = param.value

    if params:
        print(f"\nParameters: {json.dumps(params, ensure_ascii=False)}")

    # 컨텍스트 생성
    ctx = create_test_context(verbose=True, node_id=schema.name)

    # 노드 실행
    print("\n" + "=" * 50)
    print("Running node...")
    print("=" * 50)

    try:
        node_instance = node_class()
        start_time = time.time()
        result = node_instance.run(inputs=inputs, parameters=params, ctx=ctx)
        elapsed_time = time.time() - start_time

        print(f"\nExecution completed in {elapsed_time:.3f}s")

    except Exception as e:
        print(f"\n[ERROR] 노드 실행 중 오류 발생: {e}", file=sys.stderr)
        if verbose:
            import traceback

            traceback.print_exc()
        return 1

    # 결과 검증
    if not isinstance(result, dict):
        print(
            f"\n[WARNING] run()이 dict를 반환하지 않았습니다. 반환 타입: {type(result).__name__}"
        )

    # 결과 출력
    if result:
        _print_result(result)

    # 결과 저장
    if output_file and result:
        try:
            _save_output(output_file, result)
        except ValueError as e:
            print(f"\n[ERROR] {e}", file=sys.stderr)
            return 1

    # 성공
    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)

    return 0


def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    """test 서브커맨드 파서를 설정합니다."""
    parser = subparsers.add_parser(
        "test",
        help="커스텀 노드를 로컬에서 테스트합니다.",
        description="커스텀 노드 파일을 로드하고 스키마 검증 및 실행 테스트를 수행합니다.",
    )

    parser.add_argument(
        "node_file",
        help="테스트할 노드 파일 경로 (예: hello_node.py)",
    )

    parser.add_argument(
        "--class",
        dest="class_name",
        help="테스트할 노드 클래스 이름 (파일에 여러 노드가 있을 경우)",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="스키마 검증만 수행하고 실행하지 않음",
    )

    parser.add_argument(
        "--input", "-i",
        help="입력 데이터 파일 경로 (JSON 또는 CSV)",
    )

    parser.add_argument(
        "--params", "-p",
        help='파라미터 JSON 문자열 (예: \'{"message": "Hello"}\')',
    )

    parser.add_argument(
        "--output", "-o",
        help="결과를 저장할 파일 경로 (JSON 또는 CSV)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세 출력 모드",
    )

    parser.set_defaults(func=run_test)
