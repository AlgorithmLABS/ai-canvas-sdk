# 첫 번째 노드 만들기

숫자 컬럼을 기준으로 행을 걸러 내는 노드를 만들고, CLI로 스키마·실행까지 확인합니다.

## 목표

- 입력: DataFrame (`input_data`)
- 출력: 필터된 DataFrame (`filtered`) + 건수 요약 (`summary`, DISPLAY 포트)
- 파라미터: `column`, `threshold`, `op` (`gte` / `lte`)

## 노드 코드

`filter_node.py`:

```python
from __future__ import annotations

import pandas as pd

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


class FilterRowsNode(CustomNode):
    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="FilterRows",
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
                    ),
                ],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="filtered",
                    ),
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DISPLAY,
                        label="summary",
                    ),
                ],
                params=[
                    Parameter(
                        text="컬럼",
                        name="column",
                        form_type="input",
                        value="score",
                    ),
                    Parameter(
                        text="임계값",
                        name="threshold",
                        form_type="number",
                        value=90,
                    ),
                    Parameter(
                        text="비교",
                        name="op",
                        form_type="select",
                        value="gte",
                        options={
                            "items": [
                                {"label": "이상", "value": "gte"},
                                {"label": "이하", "value": "lte"},
                            ]
                        },
                    ),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs.get("input_data")
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("input_data 가 비어 있습니다")

        column = parameters.get("column", "score")
        threshold = float(parameters.get("threshold", 0))
        op = parameters.get("op", "gte")

        if column not in df.columns:
            raise ValueError(f"컬럼이 없습니다: {column}")

        ctx.log_info(f"filter {column} {op} {threshold}")
        series = pd.to_numeric(df[column], errors="coerce")
        mask = series >= threshold if op == "gte" else series <= threshold
        filtered = df.loc[mask].copy()
        ctx.progress(1.0)

        return {
            "filtered": filtered,
            "summary": {
                "input_rows": int(len(df)),
                "output_rows": int(len(filtered)),
                "column": column,
                "op": op,
                "threshold": threshold,
            },
        }
```

SDK는 `validate()` / `cleanup()` 훅을 호출하지 않습니다. 입력 검사는 `run()` 안에서 하고, 실패 시 예외를 던지면 CLI가 `[ERROR]` 로 종료합니다.

## CLI로 검증

입력 파일 `scores.json`:

```json
{
  "input_data": [
    {"name": "Ada", "score": 91},
    {"name": "Grace", "score": 88},
    {"name": "Linus", "score": 95}
  ]
}
```

```bash
# 스키마만
ai-canvas-sdk test filter_node.py --validate-only

# 실행 (기본 파라미터: score >= 90)
ai-canvas-sdk test filter_node.py -i scores.json -o filtered.json -v

# 파라미터 덮어쓰기
ai-canvas-sdk test filter_node.py \
  -i scores.json \
  -p '{"column": "score", "threshold": 88, "op": "gte"}'
```

JSON 출력을 쓰면 모든 포트가 저장됩니다. CSV 출력(`-o result.csv`)은 **첫 번째 DataFrame 포트만** 저장합니다.

## 등록으로 넘어가기 전에

로컬 `test` 는 백엔드·Secret Store·gRPC 런타임에 연결하지 않습니다. 캔버스에 올리려면 노드를 `<NodeSchema.name>/main.py` 레이아웃으로 옮긴 뒤 CI에서 `ai-canvas-sdk register` 를 탑니다. → [CI 등록 가이드](../ci/README.md)
