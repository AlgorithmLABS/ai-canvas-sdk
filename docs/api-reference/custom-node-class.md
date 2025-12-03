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

## **추상 메서드 (필수 구현)**

### **`get_schema()` (정적 메서드)**

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
def get_schema() -> NodeSchema:
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
def get_schema() -> NodeSchema:
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
def run(self, input: PortType, parameters: Dict[str, Any], ctx: NodeContext) -> tuple[PortType,Any]:
    """노드 실행 메서드

    Args:
        input: 입력 포트 타입
        parameters: 사용자 설정 파라미터
            - key: 파라미터 이름 (str)
            - value: 파라미터 값 (Any)
        ctx: 실행 컨텍스트(NodeContext)
            - log_info/warn/error, progress, emit(스트리밍), metrics, cancel_requested

    Returns:
         tuple[PortType,Any]: 출력 포트 타입

    Raises:
        ValueError: 입력 데이터가 유효하지 않은 경우
        NodeExecutionError: 실행 중 오류 발생 시
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

### **`cleanup()`**

리소스 정리를 수행합니다.

```python
def cleanup(self) -> None:
    """리소스 정리 (선택적 구현)

    노드 실행 완료 후 또는 오류 발생 시 호출됩니다.
    파일 핸들, 네트워크 연결 등을 정리할 때 사용합니다.
    """
    pass

```

**예시**:

```python
def cleanup(self) -> None:
    # 임시 파일 삭제
    if hasattr(self, 'temp_files'):
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except OSError:
                pass

    # 네트워크 연결 종료
    if hasattr(self, 'connection'):
        self.connection.close()

```

### **`log_info()`, `log_warning()`, `log_error()`**

구조화된 로깅을 수행합니다.

```python
def log_info(self, message: str, extra: Dict[str, Any] = None) -> None:
    """정보 로그 기록"""

def log_warning(self, message: str, extra: Dict[str, Any] = None) -> None:
    """경고 로그 기록"""

def log_error(self, message: str, extra: Dict[str, Any] = None) -> None:
    """에러 로그 기록"""

```

**사용 예시**:

```python
def execute(self, inputs, parameters):
    self.log_info("노드 실행 시작", {
        'input_size': len(inputs.get('data', [])),
        'parameters': parameters
    })

    try:
        result = self.process_data(inputs, parameters)
        self.log_info("처리 완료", {'output_size': len(result)})
        return result

    except Exception as e:
        self.log_error("처리 실패", {
            'error_type': type(e).__name__,
            'error_message': str(e)
        })
        raise

```

## **데코레이터**

### **`@timeout(seconds)`**

실행 시간 제한을 설정합니다.

```python
from ai_canvas_sdk.decorators import timeout

@timeout(seconds=300)
class LongRunningNode(CustomNode):
    def execute(self, inputs, parameters):
        # 최대 5분 실행
        time.sleep(600)  # TimeoutError 발생
        return {'result': 'done'}

```

### **`@cache_results(ttl_seconds)`**

결과를 캐시합니다.

```python
from ai_canvas_sdk.decorators import cache_results

@cache_results(ttl_seconds=3600)  # 1시간 캐시
class CachedNode(CustomNode):
    def execute(self, inputs, parameters):
        # 동일한 입력에 대해서는 캐시된 결과 반환
        expensive_result = self.expensive_computation(inputs)
        return {'result': expensive_result}

```

## **예외 클래스**

### **`NodeException`**

노드 실행 관련 기본 예외입니다.

```python
class NodeException(Exception):
    def __init__(self, message: str, error_type: str = None,
                 retryable: bool = False, suggestions: List[str] = None):
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable
        self.suggestions = suggestions or []

```

**사용 예시**:

```python
def execute(self, inputs, parameters):
    if 'required_data' not in inputs:
        raise NodeException(
            message="필수 입력 데이터가 없습니다",
            error_type="MISSING_INPUT",
            suggestions=["'required_data' 포트를 연결해주세요"]
        )

```

### **기타 예외들**

```python
class DataValidationError(NodeException):
    """데이터 검증 실패"""
    pass

class ResourceError(NodeException):
    """리소스 부족"""
    def __init__(self, message: str):
        super().__init__(message, error_type="RESOURCE_ERROR", retryable=True)

class ConfigurationError(NodeException):
    """설정 오류"""
    pass

```

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