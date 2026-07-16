# 빠른 시작 가이드

5분 만에 첫 번째 AI Canvas 커스텀 노드를 만들고 실행해보세요.

## 목표

이 가이드를 완료하면:
- 간단한 텍스트 처리 노드 생성
- 로컬에서 노드 테스트

## 전제 조건

- [설치 가이드](./installation.md)에 따라 SDK 설치 완료
- Python 3.10+ 환경

## Step 1: 첫 번째 노드 생성

`hello_node.py` 파일을 생성합니다:

```python
import pandas as pd
from ai_canvas_sdk import (
    CustomNode, NodeContext, NodeData, NodeSchema,
    Parameter, Port, PortEnum, PortTypeEnum, PositionEnum,
)


class HelloWorldNode(CustomNode):
    """간단한 텍스트 처리 노드"""

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="HelloWorld",
            category="text_processing",
            data=NodeData(
                input_ports=[],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="output_text",
                    ),
                ],
                params=[
                    Parameter(
                        text="인사말",
                        name="greeting",
                        form_type="input",
                        value="Hello",
                        value_type="string",
                        is_tab=True,
                    ),
                    Parameter(
                        text="이름",
                        name="user_name",
                        form_type="input",
                        value="Hong",
                        value_type="string",
                        is_tab=True,
                    ),
                ],
            ),
            version="1.0.0",
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        """노드 실행 로직"""
        user_name = parameters.get("user_name", "Hong")
        greeting = parameters.get("greeting", "Hello")

        # 비즈니스 로직
        df = pd.DataFrame({
            "name": [user_name],
            "greeting": [f"{greeting} {user_name}"],
        })

        # 결과 반환 — 출력 포트 label을 key로 하는 dict
        return {"output_text": df}


node = HelloWorldNode()
```

## Step 2: 데이터프레임 노드 예제

DataFrame 처리 노드를 만들어보겠습니다:

`data_filter_node.py`:

```python
import pandas as pd
from ai_canvas_sdk import (
    CustomNode, NodeContext, NodeData, NodeSchema,
    Parameter, Port, PortEnum, PortTypeEnum, PositionEnum,
)


class DataFilterNode(CustomNode):
    """데이터 필터링 노드"""

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="DataFilter",
            category="data_processing",
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
                        label="filtered_data",
                    ),
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DISPLAY,
                        label="stats",
                    ),
                ],
                params=[
                    Parameter(
                        text="필터 컬럼",
                        name="column",
                        form_type="input",
                        value_type="string",
                        is_tab=True,
                    ),
                    Parameter(
                        text="임계값",
                        name="threshold",
                        form_type="number",
                        value=0,
                        value_type="number",
                        is_tab=True,
                    ),
                ],
            ),
            version="1.0.0",
        )

    def validate(self, inputs: dict, parameters: dict) -> None:
        """입력 검증"""
        df = inputs["input_data"]
        column = parameters.get("column")

        if df is None or df.empty:
            raise ValueError("입력 데이터가 비어있습니다")

        if column not in df.columns:
            raise ValueError(f"컬럼 '{column}'이 데이터에 존재하지 않습니다")

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs["input_data"]
        column = parameters["column"]
        threshold = parameters.get("threshold", 0)

        # 데이터 필터링
        filtered_df = df[df[column] > threshold]

        # 통계 생성
        stats_df = pd.DataFrame([{
            "original_rows": len(df),
            "filtered_rows": len(filtered_df),
            "filter_ratio": len(filtered_df) / len(df) if len(df) > 0 else 0,
            "column": column,
            "threshold": threshold,
        }])

        # 결과 반환 — 출력 포트 label(filtered_data, stats)을 key로 하는 dict
        return {"filtered_data": filtered_df, "stats": stats_df}


node = DataFilterNode()
```

### 데이터프레임 테스트

```bash
# 스키마만 먼저 검증 (실제 데이터 없이)
ai-canvas-sdk test data_filter_node.py --validate-only
```

스키마가 맞는지 먼저 확인한 뒤, `-i`와 `-p`로 실제 입력을 주고 다시 실행합니다.

```bash
ai-canvas-sdk test data_filter_node.py -i input.json -p '{"column": "value", "threshold": 0.5}'
```

## Step 3: 로컬 테스트 반복

```python
# large_data_test.py
import numpy as np
import pandas as pd
from ai_canvas_sdk import NodeContext
from data_filter_node import node

# 10만 행 샘플 데이터 생성
large_df = pd.DataFrame({
    "value": np.random.uniform(0, 1, size=100_000),
})

# 노드 테스트
ctx = NodeContext(execution_id="local-test", node_id="data-filter")
result = node.run(
    inputs={"input_data": large_df},
    parameters={"column": "value", "threshold": 0.5},
    ctx=ctx,
)

print(f"처리된 행 수: {len(result['filtered_data'])}")
print(f"통계: {result['stats']}")
```

## 완료!

축하합니다! 첫 번째 AI Canvas 커스텀 노드를 성공적으로 만들고 실행했습니다.


### 학습 팁

- **작게 시작**: 간단한 기능부터 구현
- **자주 테스트**: `ai-canvas-sdk test` 명령을 활용
- **로그 확인**: 노드 안에서 `ctx.log_info()` 등으로 로그를 남기고, `ai-canvas-sdk test`에 `-v` 옵션을 주면 실행 중 로그를 함께 확인할 수 있습니다.
