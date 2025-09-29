# CustomNode 클래스 API 레퍼런스

`CustomNode`는 모든 커스텀 노드가 상속받아야 하는 기본 클래스입니다.

## 클래스 정의

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class CustomNode(ABC):
    """커스텀 노드 기본 클래스"""
    
    def __init__(self):
        """노드 인스턴스 초기화"""
        self._execution_context: Optional[ExecutionContext] = None
        self._progress_tracker: Optional[ProgressTracker] = None
        self._resource_manager: Optional[ResourceManager] = None
```

## 추상 메서드 (필수 구현)

### `get_schema()` (정적 메서드)

노드의 메타데이터를 정의합니다.

```python
@staticmethod
@abstractmethod
def get_schema() -> NodeSchema:
    """노드 스키마 정의
    
    Returns:
        NodeSchema: 노드의 메타데이터 스키마
    """
    pass
```

**예시**:
```python
@staticmethod
def get_schema() -> NodeSchema:
    return NodeSchema(
        name="MyNode",
        display_name="나의 노드",
        description="노드 설명",
        inputs=[...],
        outputs=[...],
        parameters=[...]
    )
```

### `run()`

노드의 실제 실행 로직을 구현합니다.

```python
@abstractmethod
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
def run(self, input: PortType.Dataset, parameters: Dict[str, Any], ctx: NodeContext) -> tuple[PortType.Dataset,PortType.Display]:
    # 입력 데이터 가져오기
    df = inputs['input_data']
    threshold = parameters.get('threshold', 0.5)
    
    # 비즈니스 로직 수행
    filtered_df = df[df['value'] > threshold]
    
    # 결과 반환
    return (
        Dataset(filtered_df),
        Display('summary': {'filtered_rows': len(filtered_df)})
    )

```

## 선택적 메서드

### `validate()`

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

### `cleanup()`

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

### `log_info()`, `log_warning()`, `log_error()`

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

## 데코레이터

### `@timeout(seconds)`

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

### `@cache_results(ttl_seconds)`

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

## 예외 클래스

### `NodeException`

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

### 기타 예외들

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

## 완전한 노드 예시

```python
from ai_canvas_sdk import CustomNode, NodeSchema, PortType
from ai_canvas_sdk.decorators import timeout
from typing import Dict, Any
import pandas as pd
import logging


@timeout(seconds=300)
class CompleteExampleNode(CustomNode):
    """완전한 예시 노드"""
    
    def __init__(self):
        super().__init__()
        self.DEFAULT_THRESHOLD = 0.5
    
    @staticmethod
    def get_schema() -> NodeSchema:
        return NodeSchema(
            name="CompleteExample",
            display_name="완전한 예시 노드",
            description="노드 개발의 모든 패턴을 보여주는 예시",
            category="examples",
            version="1.0.0",
            
            inputs=[{
                "name": "input_data",
                "display_name": "입력 데이터",
                "type": PortType.DATAFRAME,
                "required": True,
                "description": "처리할 DataFrame"
            }],
            
            outputs=[{
                "name": "processed_data", 
                "display_name": "처리된 데이터",
                "type": PortType.DATAFRAME,
                "description": "처리 결과"
            }],
            
            parameters=[{
                "name": "threshold",
                "display_name": "임계값",
                "type": "number",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0
            }]
        )
    
    def validate(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        df = inputs.get('input_data')
        if df is None or df.empty:
            raise ValueError("입력 데이터가 비어있습니다")
        
        if 'value' not in df.columns:
            raise ValueError("'value' 컬럼이 필요합니다")
    
    def execute(self, input:PortType.Dataset, parameters: Dict[str, Any]) -> tuple[PortType.Dataset,Any]:
        self.log_info("노드 실행 시작")
        
        # 진행 상황 추적 설정
        progress = self.get_progress_tracker()
        progress.set_total_steps(3)
        
        # 1단계: 데이터 준비
        progress.advance("데이터 준비 중...")
        df = inputs.copy()
        threshold = parameters.get('threshold', self.DEFAULT_THRESHOLD)
        
        # 2단계: 데이터 처리
        progress.advance("데이터 처리 중...")
        processed_df = df[df['value'] > threshold]
        
        # 3단계: 완료
        progress.advance("완료")
        
        self.log_info("처리 완료", {
            'input_rows': len(df),
            'output_rows': len(processed_df)
        })
        
        return (Dataset(dataframe=processed_df),)
    
    def cleanup(self) -> None:
        self.log_info("리소스 정리 완료")

# 노드 인스턴스 생성
node = CompleteExampleNode()
```

---

이 API 레퍼런스를 통해 `CustomNode` 클래스의 모든 기능을 활용하여 강력하고 안정적인 커스텀 노드를 개발할 수 있습니다.