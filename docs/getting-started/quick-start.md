# 빠른 시작 가이드

몇 분 안에 커스텀 노드를 만들고 `ai-canvas-sdk test` 로 로컬 실행까지 확인합니다.

## 전제 조건

- [설치 가이드](./installation.md)대로 SDK가 설치되어 있고 `ai-canvas-sdk --version` 이 버전 문자열을 출력한다
- Python 3.10+

## Step 1: 노드 파일 작성

`hello_node.py`:

```python
from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    NodeData,
    NodeSchema,
    Parameter,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
)
import pandas as pd


class HelloWorldNode(CustomNode):
    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="HelloWorld",
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
                        label="output_data",
                    ),
                ],
                params=[
                    Parameter(
                        text="인사말",
                        name="greeting",
                        form_type="input",
                        value="Hello",
                    ),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs["input_data"].copy()
        greeting = parameters.get("greeting", "Hello")
        ctx.log_info(f"processing {len(df)} rows")
        ctx.progress(1.0)
        df["greeting"] = greeting
        return {"output_data": df}
```

같은 내용이 저장소의 [`docs/examples/hello_node.py`](../examples/hello_node.py) 에도 있습니다.

계약:

- `get_schema()` 는 **인스턴스 메서드**입니다 (`@staticmethod` 아님).
- `run(self, inputs, parameters, ctx)` 시그니처를 지켜야 합니다. `inputs` / 반환 dict 의 키는 포트 `label` 입니다.
- 스키마는 `NodeSchema(name=..., data=NodeData(input_ports=..., output_ports=..., params=...))` 입니다. `inputs=` / `display_name=` / `PortType` 같은 옛 필드는 없습니다.

## Step 2: 스키마만 검증

```bash
ai-canvas-sdk test hello_node.py --validate-only
```

성공 시 `Result: VALID` 와 포트/파라미터 요약이 나옵니다. 이 단계에서는 `run()` 을 호출하지 않습니다.

## Step 3: 입력과 파라미터로 실행

`hello_input.json`:

```json
{
  "input_data": [
    {"name": "Ada", "score": 91},
    {"name": "Grace", "score": 88}
  ]
}
```

```bash
ai-canvas-sdk test hello_node.py \
  -i hello_input.json \
  -p '{"greeting": "Hi"}' \
  -o hello_out.json \
  -v
```

- `-i` 의 JSON 키는 입력 포트 `label` (`input_data`) 입니다. 배열은 DataFrame 행이 됩니다.
- `-p` 의 키는 파라미터 `name` (`greeting`) 입니다. 생략하면 스키마의 `Parameter.value` 기본값이 쓰입니다.
- `-o` 는 출력 DataFrame 을 JSON 레코드로 저장합니다.
- `-v` 는 스키마 경고까지 출력합니다. `ctx.log_*` / `ctx.progress` 는 **stderr** 로 나갑니다 (`~/.ai-canvas/sdk.log` 파일은 없습니다).

`-i` 를 생략하면 각 입력 포트에 **빈 DataFrame** 이 들어갑니다.

## 다음 단계

- [로컬 CLI 테스트](../guides/local-cli-testing.md) — 입력 형식, secret 주입, 클래스 지정
- [첫 번째 노드 만들기](./first-node.md) — 필터 노드 + 입력 검증
- [Secret 사용](../guides/using-secrets.md) — `required_secrets` / `-s KEY=VALUE`
