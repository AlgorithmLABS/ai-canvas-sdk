# CustomNode 클래스 API 레퍼런스

공개 패키지에서 import 하는 계약입니다.

```python
from ai_canvas_sdk import (
    CustomNode,
    CustomNodeError,
    NodeContext,
    NodeData,
    NodeMetadata,
    NodeSchema,
    Parameter,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
    SecretNotAvailableError,
)
```

`PortType`, `Dataset`, `ai_canvas_sdk.testing` 은 존재하지 않습니다.

## CustomNode

사용자는 이 클래스를 상속해 **`get_schema()` 와 `run()`** 을 구현합니다. `validate()` 는 추상 메서드가 아니며 SDK가 호출하지 않습니다.

```python
class CustomNode(ABC):
    required_secrets: list[str] = []

    @abstractmethod
    def get_schema(self) -> NodeSchema: ...

    @abstractmethod
    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict: ...
```

### `required_secrets`

실행 시 `ctx.get_secret(name)` 으로 받을 이름 목록입니다. **클래스 속성 리터럴**이어야 합니다. 등록 시 AST 로 추출되므로 `build_names()` 나 `self.required_secrets = ...` 는 무시됩니다.

```python
class WeatherNode(CustomNode):
    required_secrets = ["weather_api_key"]
```

값은 코드에 두지 않습니다. 흐름은 [Secret 사용 가이드](../guides/using-secrets.md).

### `get_schema(self) -> NodeSchema`

인스턴스 메서드입니다. `@staticmethod` 가 아닙니다.

필수: `name`, `data`.

```python
def get_schema(self) -> NodeSchema:
    return NodeSchema(
        name="HelloNode",
        data=NodeData(
            input_ports=[
                Port(
                    type=PortEnum.TARGET,
                    position=PositionEnum.LEFT,
                    port_type=PortTypeEnum.DATASET,
                    label="input_dataset",
                    required=True,
                )
            ],
            output_ports=[
                Port(
                    type=PortEnum.SOURCE,
                    position=PositionEnum.RIGHT,
                    port_type=PortTypeEnum.DATASET,
                    label="output_dataset",
                )
            ],
            params=[
                Parameter(
                    text="메시지",
                    name="message",
                    form_type="input",
                    value="Hello World!",
                )
            ],
        ),
        version="1.0.0",
    )
```

### `run(self, inputs, parameters, ctx) -> dict`

| 인자 | 내용 |
|------|------|
| `inputs` | `{포트 label: 값}`. DATASET 은 주로 `pandas.DataFrame` |
| `parameters` | `{Parameter.name: 값}` |
| `ctx` | `NodeContext` — 로그, 진행률, 취소, secret |

반환 dict 키는 출력 포트 `label` 이어야 합니다.

```python
def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
    df = inputs.get("input_dataset")
    if df is None:
        return {"output_dataset": pd.DataFrame()}
    message = parameters.get("message", "")
    out = df.copy()
    out["result"] = message
    ctx.log_info("done")
    ctx.progress(1.0)
    return {"output_dataset": out}
```

## NodeSchema / NodeData / NodeMetadata

```python
@dataclass
class NodeData:
    input_ports: list[Port]
    output_ports: list[Port]
    params: list[Parameter] = field(default_factory=list)

@dataclass
class NodeMetadata:
    author: str = ""
    license: str = ""
    documentation_url: str = ""
    source_code_url: str = ""
    custom_metadata: dict = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

@dataclass
class NodeSchema:
    name: str
    data: NodeData
    category: str = "custom"
    width: int = 200
    height: int = 142
    version: str = "1.0.0"
    metadata: NodeMetadata | None = None
    source_code: str = ""
    entry_class: str = ""
    dependencies: list[str] = field(default_factory=list)
```

`display_name` 필드는 없습니다. 캔버스 표시는 주로 `name` 과 파라미터 `text` 를 씁니다.

CI 등록 시 폴더명과 `NodeSchema.name` 리터럴이 같아야 합니다. → [CI 가이드](../ci/README.md)

## Port

```python
class PortEnum(Enum):
    SOURCE = "source"
    TARGET = "target"

class PositionEnum(Enum):
    RIGHT = "right"
    LEFT = "left"
    TOP = "top"
    BOTTOM = "bottom"

class PortTypeEnum(Enum):
    DATASET = "dataset"
    UNTRAINED = "untrainedModel"
    TRAINED = "trainedModel"
    TRANSFORMER = "transformer"
    DISPLAY = "display"

@dataclass
class Port:
    type: PortEnum
    position: PositionEnum
    port_type: PortTypeEnum
    label: str | None = None
    required: bool = True
```

- 입력 포트: `type=TARGET`. CLI 검증기는 `LEFT`/`TOP` 을 권장.
- 출력 포트: `type=SOURCE`. `RIGHT`/`BOTTOM` 권장.
- 출력 포트의 `required` 는 사용되지 않습니다.
- `JSON` 포트 타입은 없습니다. 요약 dict 는 `DISPLAY` 로 두거나 DATASET 컬럼으로 넣습니다.

## Parameter

```python
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
```

| 필드 | 의미 |
|------|------|
| `name` | `run()` / CLI `-p` 의 키 |
| `text` | UI 라벨. 런타임 키가 아님 |
| `form_type` | 캔버스 폼 종류 |
| `value` | 기본값 |
| `value_type` | `string` / `number` / `boolean` / `object` / `stringArray` / `numberArray` / `objectArray` / `unknown`. 공개 `__init__` 으로는 export 되지 않으므로 생략하면 STRING |
| `is_tab` | `True` 이면 오른쪽 파라미터 탭에 표시 |

## NodeContext

```python
ctx.execution_id
ctx.node_id
ctx.user_id
ctx.team_id

ctx.log_debug / log_info / log_warning / log_error / log_critical(message: str)
ctx.progress(percentage: float)          # 0.0 ~ 1.0
ctx.is_cancelled() -> bool
ctx.get_secret(name: str) -> str         # 없으면 SecretNotAvailableError
```

로컬 `ai-canvas-sdk test` 는 stderr 로 로그·진행률을 찍는 테스트 컨텍스트를 씁니다. `emit` / `metrics` / `cancel_requested` 같은 이름은 없습니다.

생성자:

```python
NodeContext(
    execution_id: str,
    node_id: str,
    user_id: str | None = None,
    team_id: str | None = None,
    secrets: dict[str, str] | None = None,
)
```

## 예외

- `CustomNodeError` — SDK 기본 예외
- `SecretNotAvailableError` — `get_secret` 대상이 컨텍스트에 없을 때. 메시지에 값 없음, 이름만

## SDK가 제공하지 않는 훅

문서 초안에 있던 다음 API 는 **구현되어 있지 않습니다.**

- `CustomNode.validate(...)` 를 SDK가 호출
- `CustomNode.cleanup()`
- `self.log_info` / `execute()`
- `run(...) -> tuple[PortType, Any]`
