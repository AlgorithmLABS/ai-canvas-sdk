# **CustomNode 클래스 API 레퍼런스**

`CustomNode`는 모든 커스텀 노드가 상속받아야 하는 기본 클래스입니다.

## **클래스 정의**

```python
from abc import ABC, abstractmethod

class CustomNode(ABC):
    """
    커스텀 노드 기본 클래스
    사용자는 이 클래스를 상속받아 다음 메서드를 구현해야 합니다:
      1. get_schema(): 노드 스키마 정의 (이름, 포트, 파라미터 등)
      2. run(): 노드 실행 로직
      3. validate(): 입력 검증 (선택적)

    """

    # 이 노드가 요구하는 동적 secret 이름 목록 (선택적 override)
    required_secrets: list[str] = []

    @abstractmethod
    def get_schema(self) -> NodeSchema:
        """
        노드 스키마를 반환.

        노드의 이름, 포트, 파라미터, 메타데이터 등을 정의.
        이 정보는 노드 등록 시 backend와 ai_canvas_cne 에 전달됨.

        returns:
            NodeSchema: 노드 스키마
        """
        pass

    @abstractmethod
    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        """
        노드를 실행합니다.

        입력 포트의 데이터와 파라미터를 받아 노드를 실행.

        Args:
            inputs (dict): 입력 포트 데이터
                - key: 입력 포트 label (예: "input_data")
                - value: 데이터 (주로 pandas.DataFrame, 또는 dict)
                - 예: {"input_data": pd.DataFrame(...)}

            parameters (dict): 파라미터 값
                - key: 파라미터 name (예: "multiplier")
                - value: 파라미터 value (타입 : number, string, boolean, object, stringArray, numberArray, objectArray)
                - 예: {"multiplier": 2.0, "method": "mean"}

              ctx (NodeContext): 실행 컨텍스트
                  - 로그 출력: ctx.log_info("message"), ctx.log_error("error") 등
                  - 진행률 보고: ctx.progress(0.5)  # 0.0 ~ 1.0
                  - 취소 확인: if ctx.is_cancelled(): raise Exception("Cancelled")
                  - 실행 정보: ctx.execution_id, ctx.user_id, ctx.node_id 등

          Returns:
              dict: 출력 포트 데이터
                  - key: 출력 포트 label (예: "output_data")
                  - value: 결과 데이터 (주로 pandas.DataFrame)
                  - 예: {"output_data": result_df}

          Raises:
              ValueError: 입력 데이터나 파라미터가 잘못된 경우
              Exception: 실행 중 에러 발생 시

          Example:
              ```python
              def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:

                  # 입력 가져오기
                  df = inputs['input_data']
                  multiplier = parameters.get('multiplier', 1.0)

                  # 처리
                  ctx.progress(0.5)
                  result = df * multiplier

                  ctx.progress(1.0)
                  ctx.log_info("Completed")

                  return {'output_data': result}
              ```
        """
        pass

```

## **클래스 속성**

### **`required_secrets` (선택적)**

노드가 실행 시 필요로 하는 **동적 secret 이름 목록**입니다. API 키·토큰처럼 코드에 하드코딩하면 안 되는 값을, 플랫폼 관리자가 코드 배포 없이 Secret Store에 등록·교체할 수 있게 하는 메커니즘입니다.

```python
class WeatherNode(CustomNode):
    # 이 노드가 요구하는 secret 이름을 선언한다
    required_secrets = ["weather_api_key"]
```

- **타입**: `list[str]` (기본값 `[]`)
- **선언 = 정적 추출**: 노드 등록 시 SDK가 **소스 코드를 실행하지 않고 정적(AST)으로** `required_secrets` 리터럴을 추출해 노드 메타데이터에 저장합니다. 따라서 반드시 **클래스 속성 리터럴**(문자열 리스트/튜플)이어야 하며, 동적 계산식이나 인스턴스 속성으로 만들면 추출되지 않습니다.
- **주입 = 선언된 것만**: 실행 시점에 플랫폼은 여기에 선언된 이름의 secret **값만** 컨텍스트로 주입합니다. 선언하지 않은 secret은 `ctx.get_secret()`으로 접근할 수 없습니다.
- override 시에는 **새 리스트를 할당**하세요. 공유 기본값을 `append` 등으로 in-place 변경하지 마세요.

> secret **값**은 관리자가 별도로 Secret Store에 등록합니다. 노드 코드에는 **이름만** 선언합니다. 선언 → 등록 → 소비 전체 흐름은 [Secret 사용 가이드](../guides/using-secrets.md)를 참고하세요.

### **`NodeContext.get_secret(name)`**

`run()`의 `ctx` 안에서 선언한 secret 값을 가져옵니다.

```python
def get_secret(self, name: str) -> str:
    """노드가 선언한 secret 값을 반환.

    Args:
        name: `required_secrets` 에 선언한 secret 이름

    Returns:
        str: secret 값

    Raises:
        SecretNotAvailableError: 해당 이름의 secret 이 주입되어 있지 않은 경우
    """
```

**예시**:

```python
from ai_canvas_sdk import CustomNode, NodeContext

class WeatherNode(CustomNode):
    required_secrets = ["weather_api_key"]

    def run(self, inputs, parameters, ctx: NodeContext) -> dict:
        api_key = ctx.get_secret("weather_api_key")  # 선언했고 등록된 경우에만 성공
        # ... api_key 로 외부 API 호출 ...
        return {"output_data": result}
```

- **반환은 항상 `str`** 입니다.
- `required_secrets`에 선언하지 않았거나(미주입), 관리자가 아직 Secret Store에 등록하지 않은 경우 `SecretNotAvailableError`가 발생합니다.
- **secret 값을 로그로 출력하지 마세요.** `ctx.log_info(api_key)` 같은 호출은 값이 실행 로그에 남아 유출됩니다.

### **`SecretNotAvailableError`**

```python
from ai_canvas_sdk import SecretNotAvailableError
```

노드가 요청한 secret이 실행 컨텍스트에 주입되어 있지 않을 때 `ctx.get_secret(name)`이 던지는 예외입니다(`CustomNodeError` 하위). 예외 메시지에는 secret **이름만** 포함되고 값은 포함되지 않습니다.

| 발생 원인 | 해결 |
|---|---|
| `required_secrets`에 이름을 선언하지 않음 | 클래스 속성 `required_secrets` 에 해당 이름 추가 후 재등록 |
| 관리자가 Secret Store에 값을 아직 등록하지 않음 | 플랫폼 관리자에게 해당 secret 등록 요청 |

## **추상 메서드 (필수 구현)**

### **`get_schema()`**

> 이 메서드는 **인스턴스 메서드**입니다(`self` 인자를 받으며 `@staticmethod` 가 아닙니다).

노드의 메타데이터를 정의합니다.

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

```python
@abstractmethod
def get_schema(self) -> NodeSchema:
    """노드 스키마 정의

    Returns:
        NodeSchema: 노드의 메타데이터 스키마
    """
    pass

```

꼭 작성해야 하는 항목은 name, data, version 입니다. 

`name`: 노드 이름
`data`: 노드 데이터 정보

- `input_ports`: 입력 포트 목록

- `type`: 포트 타입 - `target` 으로 고정
- `position`: 포트 위치 - `left` 로 고정
- `port_type`: 포트 타입 - `dataset` ( 지원 예정 : untrainedModel, trainedModel, transformer, display )중 하나
- `label`: 포트 라벨 - 노드 실행 시 입력 데이터의 key 값으로 사용
- `required`: 포트 필수 여부 - True 또는 False (기본값 True)

- `output_ports`: 출력 포트 목록

- `type`: 포트 타입 - source 으로 고정
- `position`: 포트 위치 - right 로 고정
- `port_type`: 포트 타입 - dataset ( 지원 예정 : untrainedModel, trainedModel, transformer, display )중 하나
- `label`: 포트 라벨 - 노드 실행 시 출력 데이터의 key 값으로 사용
- `~~required`: 포트 필수 여부 - True 또는 False (기본값 True)  사용되지 않음~~

- `params`: 파라미터 목록

- `text`: 파라미터 텍스트 - 노드 실행 시 파라미터의 key 값으로 사용
- `name`: 파라미터 이름 - 노드 실행 시 파라미터의 value 값으로 사용
- `form_type`: 파라미터 폼 타입 -  다음 문서 참고 [https://www.notion.so/algorithmlabs/e4e01880a62e4a339535dde9e83aeace?v=80af52c2ce37449cb1e76e96d0b8b1d0](https://www.notion.so/e4e01880a62e4a339535dde9e83aeace?pvs=21)
- `value_type`: 파라미터 값 타입 - string, number, boolean, object, stringArray, numberArray, objectArray, unknown 중 하나
- `value`: 파라미터 값 - 파라미터 값의 기본값을 설정
- `mode`: 파라미터 모드 - 기본값 None, 다음 문서 참고 [https://www.notion.so/algorithmlabs/3da824029f164400b9582ee5ce54f93a?source=copy_link#73ea1cc34e63407db5c0187bebca1618](https://www.notion.so/3da824029f164400b9582ee5ce54f93a?pvs=21)
- `options`: 파라미터 옵션 - 기본값 None, 다음 문서 참고 [https://www.notion.so/algorithmlabs/3da824029f164400b9582ee5ce54f93a?source=copy_link#73ea1cc34e63407db5c0187bebca1618](https://www.notion.so/3da824029f164400b9582ee5ce54f93a?pvs=21)
- `is_tab`: 파라미터 탭 여부 - True, False 또는 None (기본값 None) True 인 경우에만 오른쪽 파라미터 탭에 파라미터가 표기됨.

`category`: 노드 카테고리 - custom 으로 고정
`width`: 노드 너비 - 기본값 200
`height`: 노드 높이 - 기본값 142
`version`: 노드 버전

**예시**:

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
                        text="message",
                        name="message",
                        form_type="input",
                        value_type="string",
                        value="Hello World!",
                        mode=None,
                        options=None,
                        is_tab=False,
                    )
                ],
            ),
            version="1.0.0",
        )

```

### **`run()`**

노드의 실제 실행 로직을 구현합니다.

```python
def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
    """노드 실행 메서드

    Args:
        inputs: 입력 포트 데이터 (포트 label → 값 dict, 값은 주로 pandas.DataFrame)
        parameters: 사용자 설정 파라미터
            - key: 파라미터 이름 (str)
            - value: 파라미터 값 (Any)
        ctx: 실행 컨텍스트(NodeContext)
            - log_debug/info/warning/error/critical, progress(0.0~1.0), is_cancelled(), get_secret(name)

    Returns:
         dict: 출력 포트 label 을 키로 하는 결과 dict

    Raises:
        ValueError: 입력 데이터가 유효하지 않은 경우
        Exception: 실행 중 오류 발생 시
    """
    pass

```

**예시**:

```python
def run(self, inputs, parameters, ctx):
    input_dataset = inputs.get("input_dataset", None)

    if input_dataset is None:
        return {"output_dataset": pd.DataFrame()}

    if isinstance(input_dataset, dict):
        df = pd.DataFrame(input_dataset)
    elif isinstance(input_dataset, pd.DataFrame):
        df = input_dataset.copy()
    else:
        return {"output_dataset": pd.DataFrame()}

    parameter_message = parameters.get("message", None)

    df["result"] = parameter_message

    return {"output_dataset": df}

```

## **선택적 메서드**

### **`validate()`**

입력 데이터와 파라미터 검증을 수행합니다.

```python
def validate(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> None:
    """입력 검증 (선택적 구현)

    Args:
        inputs: 입력 포트 데이터
        parameters: 파라미터

    Raises:
        ValueError: 검증 실패 시
        TypeError: 데이터 타입이 잘못된 경우
    """
    pass

```

**예시**:

```python
def validate(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> None:
    # 입력 데이터 검증
    df = inputs.get('input_data')
    if df is None or df.empty:
        raise ValueError("입력 데이터가 비어있습니다")

    # 필수 컬럼 확인
    required_cols = ['id', 'value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_cols}")

    # 파라미터 검증
    threshold = parameters.get('threshold')
    if threshold is not None and not isinstance(threshold, (int, float)):
        raise TypeError("threshold는 숫자 타입이어야 합니다")

```

### **`cleanup()` 등 기타 훅**

현재 SDK가 보장하는 실행 훅은 `get_schema()`(필수), `run()`(필수), `validate()`(선택)뿐입니다. 그 밖의 정리/캐싱/타임아웃은 노드 API가 아니라 **플랫폼 런타임의 책임**입니다.

- **리소스 정리**: 파일 핸들·네트워크 연결 등은 `run()` 내부에서 `try/finally`로 직접 정리하세요. SDK가 자동으로 호출하는 `cleanup()` 훅은 없습니다.
- **타임아웃/취소**: 플랫폼이 gRPC로 관리하며, 노드는 `ctx.is_cancelled()`로만 협조적으로 확인합니다. `@timeout`/`@cache_results` 같은 데코레이터는 존재하지 않습니다.

## **로깅·진행률·취소 (NodeContext)**

로깅·진행률·취소 확인은 노드 자체 메서드가 아니라 **`run()`에 전달되는 `ctx`(NodeContext)**로만 수행합니다.

```python
def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
    ctx.log_info("처리 시작")          # log_debug/info/warning/error/critical(message)
    ctx.progress(0.5)                  # 0.0 ~ 1.0
    if ctx.is_cancelled():             # 협조적 취소 확인
        raise RuntimeError("실행이 취소되었습니다")
    ...
```

- `ctx.log_*(message)`는 **문자열 인자 하나**만 받습니다(`extra=` 같은 인자는 없습니다).
- 진행률 `ctx.progress(pct)`의 `pct`가 0.0~1.0 범위를 벗어나면 `ValueError`가 발생합니다.

## **예외 클래스**

SDK가 제공하는 예외는 두 가지뿐입니다.

```python
from ai_canvas_sdk import CustomNodeError, SecretNotAvailableError
```

- **`CustomNodeError`**: 커스텀 노드 SDK의 기본 예외입니다. 직접 정의한 예외 타입이 필요하면 이 클래스를 상속하세요.
- **`SecretNotAvailableError`** (`CustomNodeError` 하위): `ctx.get_secret(name)`이 선언/주입되지 않은 secret에 대해 던지는 예외입니다.

입력 검증 실패 같은 일반 오류는 표준 예외(`ValueError`, `TypeError`)를 그대로 raise하면 됩니다. `NodeException`, `DataValidationError`, `ResourceError`, `ConfigurationError` 등 별도의 오류 계층은 SDK에 존재하지 않습니다.

## **완전한 노드 예시**

```python
import pandas as pd
from ai_canvas_sdk import CustomNode, NodeData, NodeSchema, Parameter, Port, PortEnum, PortTypeEnum, PositionEnum

class DataFilterNode(CustomNode):
    """데이터 필터링 노드"""

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="DataFilter",
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="input_data",
                        required=True,
                    )
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
                        port_type=PortTypeEnum.DATASET,
                        label="stats",
                    ),
                ],
                params=[
                    Parameter(
                        text="column",
                        name="column",
                        form_type="input",
                        value_type="string",
                        value="",
                        mode=None,
                        options=None,
                        is_tab=True,
                    ),
                    Parameter(
                        text="threshold",
                        name="threshold",
                        form_type="input",
                        value_type="number",
                        value=0,
                        mode=None,
                        options=None,
                        is_tab=True,
                    ),
                ],
            ),
            version="1.0.1",
        )

    def validate(self, inputs: dict, parameters: dict) -> None:
        """입력 검증"""
        df = inputs.get("input_data", None)
        column = parameters["column"]
        threshold = parameters["threshold"]

        if df is None or df.empty:
            raise ValueError("Input data is empty")

        if column not in df.columns:
            raise ValueError(f"Column '{column}' does not exist in the data")

        if not isinstance(threshold, (int, float)):
            raise ValueError("Threshold must be a number")
        if threshold < 0:
            raise ValueError("Threshold must be greater than 0")

    def run(self, inputs: dict, parameters: dict, ctx) -> dict:
        df = inputs["input_data"]
        column = parameters["column"]
        threshold = parameters.get("threshold", 0)

        # 데이터 필터링
        filtered_df = df[df[column] > threshold]

        # 통계 생성
        stats = {
            "original_rows": len(df),
            "filtered_rows": len(filtered_df),
            "filter_ratio": len(filtered_df) / len(df) if len(df) > 0 else 0,
            "column": column,
            "threshold": threshold,
        }
        stats_df = pd.DataFrame([stats])

        return {"filtered_data": filtered_df, "stats": stats_df}

```