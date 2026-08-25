# 기본 노드 개발 가이드

공개 API (`CustomNode`, `NodeSchema`, `NodeData`, `Port`, `Parameter`, `NodeContext`) 기준으로 노드를 작성합니다.

## 구현해야 하는 것

`CustomNode` 서브클래스는 다음 두 메서드만 필수입니다.

1. `get_schema(self) -> NodeSchema` — 인스턴스 메서드
2. `run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict`

SDK가 호출하지 않는 것:

- `validate()` / `cleanup()` 훅 (원하면 `run()` 안에서 직접 호출)
- `self.log_info` — 로그는 `ctx.log_info` / `ctx.log_error` …
- `@staticmethod get_schema`

## 스키마

```python
from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    NodeData,
    NodeMetadata,
    NodeSchema,
    Parameter,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
)


class TemplateNode(CustomNode):
    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="TemplateNode",
            category="custom",
            version="1.0.0",
            metadata=NodeMetadata(author="you"),
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="input_data",
                        required=True,
                    ),
                ],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="output_data",
                    ),
                ],
                params=[
                    Parameter(
                        text="임계값",          # UI 표시명
                        name="threshold",      # parameters 키
                        form_type="number",
                        value=0.5,             # CLI -p 생략 시 기본값
                    ),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs["input_data"]
        threshold = parameters.get("threshold", 0.5)
        ctx.log_info(f"rows={len(df)} threshold={threshold}")
        ctx.progress(1.0)
        return {"output_data": df}
```

### 포트

| 방향 | `type` | 권장 `position` | `run()` 키 |
|------|--------|-----------------|------------|
| 입력 | `PortEnum.TARGET` | `LEFT` 또는 `TOP` | `label` |
| 출력 | `PortEnum.SOURCE` | `RIGHT` 또는 `BOTTOM` | 반환 dict 의 `label` |

`port_type` 은 `PortTypeEnum` 만 사용합니다: `DATASET`, `UNTRAINED`, `TRAINED`, `TRANSFORMER`, `DISPLAY`. `JSON` / `DATAFRAME` / `PortType` 이름은 없습니다.

로컬 CLI에서 DATASET 입력은 pandas DataFrame 으로 들어옵니다.

### 파라미터

| 필드 | 역할 |
|------|------|
| `name` | `parameters` dict 키, CLI `-p` 키 |
| `text` | 캔버스 표시 이름 |
| `form_type` | 캔버스 폼 위젯 (`input`, `number`, `select`, …) |
| `value` | 기본값. CLI는 `-p` 에 없는 이름만 이 값으로 채움 |
| `options` | select 등 위젯 옵션 |
| `is_tab` | `True` 이면 오른쪽 파라미터 탭에 표시 |

## run() 패턴

- 입력 검사는 `run()` 초반에서. 비면 `ValueError` 를 던지면 CLI가 실패로 끝냅니다.
- 진행률은 `0.0`–`1.0`. 범위 밖은 `ValueError`.
- 취소가 필요하면 `if ctx.is_cancelled(): raise RuntimeError("cancelled")`. 로컬 테스트 컨텍스트는 항상 `False`.
- 반환은 **dict**. 키 = 출력 포트 `label`. DATASET 은 DataFrame 을 그대로 반환하면 됩니다. `Dataset(...)` 래퍼는 없습니다.

```python
def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
    df = inputs.get("input_data")
    if df is None or df.empty:
        raise ValueError("input_data 가 비어 있습니다")

    column = parameters.get("column", "value")
    if column not in df.columns:
        raise ValueError(f"없는 컬럼: {column}")

    if ctx.is_cancelled():
        raise RuntimeError("cancelled")

    ctx.progress(0.5)
    out = df.copy()
    ctx.progress(1.0)
    ctx.log_info(f"done rows={len(out)}")
    return {"output_data": out}
```

## 단일 책임

노드는 한 가지 변환만 하는 편이 캔버스에서 재사용하기 쉽습니다. 정규화·필터·집계를 한 클래스에 넣지 마세요.

## 로컬 확인

```bash
ai-canvas-sdk test template_node.py --validate-only
ai-canvas-sdk test template_node.py -i input.json -p '{"threshold": 0.5}' -v
```

입력 형식과 secret 주입은 [로컬 CLI 테스트](./local-cli-testing.md).
