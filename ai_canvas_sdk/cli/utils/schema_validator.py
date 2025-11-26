"""노드 스키마 검증 모듈."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_canvas_sdk.custom_node import CustomNode, NodeSchema


@dataclass
class ValidationResult:
    """스키마 검증 결과."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schema: NodeSchema | None = None


def validate_schema(node_class: type[CustomNode]) -> ValidationResult:
    """
    노드 스키마를 검증합니다.

    Args:
        node_class: CustomNode 서브클래스

    Returns:
        ValidationResult: 검증 결과
    """
    from ai_canvas_sdk.custom_node import NodeSchema
    from ai_canvas_sdk.custom_node.models.port import PortEnum, PortTypeEnum, PositionEnum

    errors: list[str] = []
    warnings: list[str] = []
    schema: NodeSchema | None = None

    # 1. 인스턴스 생성 테스트
    try:
        node_instance = node_class()
    except Exception as e:
        errors.append(f"노드 인스턴스 생성 실패: {e}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # 2. get_schema() 호출 테스트
    try:
        schema = node_instance.get_schema()
    except Exception as e:
        errors.append(f"get_schema() 호출 실패: {e}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # 3. 반환 타입 검증
    if not isinstance(schema, NodeSchema):
        errors.append(f"get_schema()가 NodeSchema를 반환하지 않습니다. 반환 타입: {type(schema).__name__}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # 4. 필수 필드 검증
    if not schema.name or not schema.name.strip():
        errors.append("노드 이름(name)이 비어있습니다.")

    if not schema.data:
        errors.append("노드 데이터(data)가 없습니다.")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings, schema=schema)

    # 5. 포트 검증
    input_ports = schema.data.input_ports or []
    output_ports = schema.data.output_ports or []

    if not input_ports and not output_ports:
        warnings.append("입력 포트와 출력 포트가 모두 없습니다.")

    # 입력 포트 검증
    input_labels = set()
    for i, port in enumerate(input_ports):
        port_id = f"input_ports[{i}]"

        if port.type != PortEnum.TARGET:
            errors.append(f"{port_id}: 입력 포트는 type=TARGET이어야 합니다.")

        if port.position not in [PositionEnum.LEFT, PositionEnum.TOP]:
            warnings.append(f"{port_id}: 입력 포트는 일반적으로 LEFT 또는 TOP 위치를 사용합니다.")

        if not isinstance(port.port_type, PortTypeEnum):
            errors.append(f"{port_id}: 유효하지 않은 port_type입니다.")

        if port.label:
            if port.label in input_labels:
                errors.append(f"{port_id}: 중복된 label '{port.label}'")
            input_labels.add(port.label)
        else:
            warnings.append(f"{port_id}: label이 없습니다. 기본값이 사용됩니다.")

    # 출력 포트 검증
    output_labels = set()
    for i, port in enumerate(output_ports):
        port_id = f"output_ports[{i}]"

        if port.type != PortEnum.SOURCE:
            errors.append(f"{port_id}: 출력 포트는 type=SOURCE이어야 합니다.")

        if port.position not in [PositionEnum.RIGHT, PositionEnum.BOTTOM]:
            warnings.append(f"{port_id}: 출력 포트는 일반적으로 RIGHT 또는 BOTTOM 위치를 사용합니다.")

        if not isinstance(port.port_type, PortTypeEnum):
            errors.append(f"{port_id}: 유효하지 않은 port_type입니다.")

        if port.label:
            if port.label in output_labels:
                errors.append(f"{port_id}: 중복된 label '{port.label}'")
            output_labels.add(port.label)
        else:
            warnings.append(f"{port_id}: label이 없습니다. 기본값이 사용됩니다.")

    # 6. 파라미터 검증
    params = schema.data.params or []
    param_names = set()

    for i, param in enumerate(params):
        param_id = f"params[{i}]"

        if not param.name or not param.name.strip():
            errors.append(f"{param_id}: name이 비어있습니다.")
        elif param.name in param_names:
            errors.append(f"{param_id}: 중복된 name '{param.name}'")
        else:
            param_names.add(param.name)

        if not param.text or not param.text.strip():
            warnings.append(f"{param_id}: text(표시 이름)가 비어있습니다.")

        if not param.form_type or not param.form_type.strip():
            warnings.append(f"{param_id}: form_type이 지정되지 않았습니다.")

    # 7. 버전 형식 검증
    if schema.version:
        parts = schema.version.split(".")
        if len(parts) != 3:
            warnings.append(f"버전 형식이 권장 형식(x.y.z)이 아닙니다: {schema.version}")

    # 8. run 메서드 검증
    if not callable(getattr(node_instance, "run", None)):
        errors.append("run() 메서드가 구현되지 않았습니다.")

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        schema=schema,
    )


def format_validation_result(result: ValidationResult, verbose: bool = False) -> str:
    """
    검증 결과를 포맷팅된 문자열로 변환합니다.

    Args:
        result: 검증 결과
        verbose: 상세 출력 여부

    Returns:
        포맷팅된 문자열
    """
    lines: list[str] = []

    if result.schema:
        schema = result.schema
        lines.append("=" * 50)
        lines.append("Schema Validation")
        lines.append("=" * 50)
        lines.append(f"  Node: {schema.name}")
        lines.append(f"  Version: {schema.version}")
        lines.append(f"  Category: {schema.category}")
        lines.append("")

        # 입력 포트
        if schema.data.input_ports:
            lines.append("Input Ports:")
            for port in schema.data.input_ports:
                required = "(required)" if port.required else "(optional)"
                lines.append(f"  - {port.label} ({port.port_type.value}) {required}")
            lines.append("")

        # 출력 포트
        if schema.data.output_ports:
            lines.append("Output Ports:")
            for port in schema.data.output_ports:
                lines.append(f"  - {port.label} ({port.port_type.value})")
            lines.append("")

        # 파라미터
        if schema.data.params:
            lines.append("Parameters:")
            for param in schema.data.params:
                default = f', default: "{param.value}"' if param.value else ""
                value_type = getattr(param.value_type, "value", param.value_type)
                lines.append(f"  - {param.name} ({value_type}{default})")
            lines.append("")

    # 에러
    if result.errors:
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  [ERROR] {error}")
        lines.append("")

    # 경고 (verbose 모드에서만)
    if result.warnings and verbose:
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"  [WARNING] {warning}")
        lines.append("")

    # 결과
    lines.append("-" * 50)
    if result.is_valid:
        lines.append("Result: VALID")
    else:
        lines.append("Result: INVALID")
    lines.append("-" * 50)

    return "\n".join(lines)
