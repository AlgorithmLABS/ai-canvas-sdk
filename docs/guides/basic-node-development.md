# 기본 노드 개발 가이드

커스텀 노드 개발의 핵심 패턴과 모범 사례를 상세히 설명합니다.

## 개발 원칙

### 1. 단일 책임 원칙
각 노드는 하나의 명확한 기능만 수행해야 합니다.

```python
# 좋은 예: 단일 책임
class DataNormalizationNode(CustomNode):
    """데이터 정규화만 담당"""
    def run(self, inputs, parameters, ctx: NodeContext):
        return self.normalize_data(inputs['data'])

# 나쁜 예: 여러 책임
class DataProcessingMegaNode(CustomNode):
    """너무 많은 기능을 한 번에"""
    def run(self, inputs, parameters, ctx: NodeContext):
        # 정규화, 필터링, 집계, 시각화까지...
        pass
```

### 2. 명확한 인터페이스
입력과 출력을 명확히 정의하고 문서화합니다.

```python
class WellDefinedNode(CustomNode):
    @staticmethod
    def get_schema() -> NodeSchema:
        return NodeSchema(
            name="DataAggregator",
            display_name="데이터 집계기",
            description="지정된 컬럼을 기준으로 데이터를 집계합니다",
            
            inputs=[{
                "name": "source_data",
                "display_name": "원본 데이터",
                "type": PortType.DATAFRAME,
                "required": True,
                "description": "집계할 데이터프레임 (필수: group_by 컬럼 포함)"
            }],
            
            outputs=[{
                "name": "aggregated_data", 
                "display_name": "집계된 데이터",
                "type": PortType.DATAFRAME,
                "description": "그룹별로 집계된 결과 데이터"
            }],
            
            parameters=[{
                "name": "group_by",
                "display_name": "그룹화 컬럼",
                "type": "text",
                "required": True,
                "description": "데이터를 그룹화할 컬럼명"
            }]
        )
```

## 기본 노드 구조

### 완전한 노드 템플릿

```python
from ai_canvas_sdk import CustomNode, NodeSchema, PortType, NodeContext
from typing import Dict, Any, List
import pandas as pd
import logging

# 로거 설정


class TemplateNode(CustomNode):
    """노드 개발 템플릿"""
    
    def __init__(self):
        """초기화 - 상태가 없는 것을 권장"""
        super().__init__()
        # 상수나 설정만 초기화
        self.DEFAULT_THRESHOLD = 0.5
        self.SUPPORTED_FORMATS = ['csv', 'json', 'parquet']
    
    @staticmethod
    def get_schema() -> NodeSchema:
        """노드 메타데이터 정의"""
        return NodeSchema(
            # 기본 정보
            name="TemplateNode",
            display_name="템플릿 노드",
            description="노드 개발 템플릿",
            category="utilities",
            version="1.0.0",
            author="Your Name",
            
            # 입력 정의
            inputs=[
                {
                    "name": "input_data",
                    "display_name": "입력 데이터",
                    "type": PortType.DATAFRAME,
                    "required": True,
                    "description": "처리할 데이터프레임"
                }
            ],
            
            # 출력 정의
            outputs=[
                {
                    "name": "processed_data",
                    "display_name": "처리된 데이터",
                    "type": PortType.DATAFRAME,
                    "description": "처리 결과 데이터프레임"
                },
                {
                    "name": "metadata",
                    "display_name": "메타데이터",
                    "type": PortType.JSON,
                    "description": "처리 과정의 메타데이터"
                }
            ],
            
            # 파라미터 정의
            parameters=[
                {
                    "name": "threshold",
                    "display_name": "임계값",
                    "type": "number",
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "description": "데이터 필터링 임계값"
                },
                {
                    "name": "method",
                    "display_name": "처리 방법",
                    "type": "select",
                    "options": [
                        {"label": "평균", "value": "mean"},
                        {"label": "중앙값", "value": "median"},
                        {"label": "최댓값", "value": "max"}
                    ],
                    "default": "mean",
                    "description": "집계 방법 선택"
                }
            ]
        )
    
    def validate(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        """입력 검증 (선택적 구현)"""
        
        # 1. 입력 데이터 검증
        df = inputs.get('input_data')
        if df is None or df.empty:
            raise ValueError("입력 데이터가 비어있습니다")
        
        # 2. 필수 컬럼 확인
        required_columns = ['value']  # 예시
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
        
        # 3. 데이터 타입 확인
        if not pd.api.types.is_numeric_dtype(df['value']):
            raise ValueError("'value' 컬럼은 숫자 타입이어야 합니다")
        
        # 4. 파라미터 검증
        threshold = parameters.get('threshold')
        if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
            raise ValueError("threshold는 0과 1 사이의 숫자여야 합니다")
        
        # 5. 비즈니스 로직 검증
        method = parameters.get('method')
        if method not in ['mean', 'median', 'max']:
            raise ValueError(f"지원하지 않는 방법입니다: {method}")
    
    def run(self, inputs: Dict[str, Any], parameters: Dict[str, Any], ctx: NodeContext) -> Dict[str, Any]:
        """메인 실행 로직"""
        
        logger.info("TemplateNode 실행 시작")
        
        try:
            # 1. 입력 데이터 준비
            df = inputs['input_data'].copy()  # 원본 보호를 위해 복사
            threshold = parameters.get('threshold', self.DEFAULT_THRESHOLD)
            method = parameters.get('method', 'mean')
            
            # 2. 데이터 처리
            processed_df = self._process_data(df, threshold, method)
            
            # 3. 메타데이터 생성
            metadata = self._generate_metadata(df, processed_df, parameters)
            
            # 4. 결과 반환
            result = {
                'processed_data': processed_df,
                'metadata': metadata
            }
            
            logger.info("TemplateNode 실행 완료")
            return result
            
        except Exception as e:
            logger.error(f"TemplateNode 실행 오류: {str(e)}")
            raise
    
    def _process_data(self, df: pd.DataFrame, threshold: float, method: str) -> pd.DataFrame:
        """실제 데이터 처리 로직"""
        
        # 임계값 기준 필터링
        filtered_df = df[df['value'] > threshold]
        
        # 집계 처리
        if method == 'mean':
            result = filtered_df.groupby('category')['value'].mean().reset_index()
        elif method == 'median':
            result = filtered_df.groupby('category')['value'].median().reset_index()
        elif method == 'max':
            result = filtered_df.groupby('category')['value'].max().reset_index()
        
        return result
    
    def _generate_metadata(self, original_df: pd.DataFrame, 
                          processed_df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터 생성"""
        
        return {
            'original_rows': len(original_df),
            'processed_rows': len(processed_df),
            'reduction_ratio': len(processed_df) / len(original_df) if len(original_df) > 0 else 0,
            'parameters_used': parameters,
            'processing_timestamp': pd.Timestamp.now().isoformat(),
            'columns_processed': list(processed_df.columns)
        }
    
    def cleanup(self) -> None:
        """리소스 정리 (선택적 구현)"""
        # 필요한 경우 리소스 정리
        logger.info("TemplateNode 정리 완료")

# 노드 인스턴스 생성 (SDK가 자동 감지)
node = TemplateNode()
```

## 데이터 처리 패턴

### 1. 안전한 DataFrame 처리

```python
class SafeDataFrameProcessor:
    """안전한 DataFrame 처리 유틸리티"""
    
    @staticmethod
    def safe_copy(df: pd.DataFrame) -> pd.DataFrame:
        """메모리 효율적인 복사"""
        if df.memory_usage(deep=True).sum() > 100_000_000:  # 100MB
            logger.warning("Large DataFrame detected, consider streaming")
        return df.copy()
    
    @staticmethod
    def safe_column_access(df: pd.DataFrame, column: str, default_value=None):
        """안전한 컬럼 접근"""
        if column not in df.columns:
            if default_value is not None:
                return pd.Series([default_value] * len(df), name=column)
            else:
                raise KeyError(f"Column '{column}' not found in DataFrame")
        return df[column]
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: str = 'drop') -> pd.DataFrame:
        """결측값 처리"""
        if strategy == 'drop':
            return df.dropna()
        elif strategy == 'fill_mean':
            return df.fillna(df.mean())
        elif strategy == 'fill_zero':
            return df.fillna(0)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

# 사용 예시
class DataProcessingNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        df = SafeDataFrameProcessor.safe_copy(inputs['data'])
        
        # 안전한 컬럼 접근
        values = SafeDataFrameProcessor.safe_column_access(df, 'value')
        
        # 결측값 처리
        clean_df = SafeDataFrameProcessor.handle_missing_values(df, 'fill_mean')
        
        return {'clean_data': clean_df}
```

### 2. 메모리 효율적인 처리

```python
class MemoryEfficientNode(CustomNode):
    """메모리 효율적인 노드"""
    
    def run(self, inputs, parameters, ctx: NodeContext):
        df = inputs['large_dataset']
        chunk_size = parameters.get('chunk_size', 10000)
        
        # 청크 단위 처리로 메모리 절약
        results = []
        
        for start in range(0, len(df), chunk_size):
            chunk = df.iloc[start:start + chunk_size]
            
            # 청크 처리
            processed_chunk = self.process_chunk(chunk, parameters)
            results.append(processed_chunk)
            
            # 메모리 정리 (선택적)
            del chunk
        
        # 결과 병합
        final_result = pd.concat(results, ignore_index=True)
        
        return {'processed_data': final_result}
    
    def process_chunk(self, chunk: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
        """청크별 처리 로직"""
        # 실제 처리 로직
        return chunk[chunk['value'] > parameters.get('threshold', 0)]
```

### 3. 데이터 타입 변환

```python
class DataTypeConverter:
    """데이터 타입 변환 유틸리티"""
    
    @staticmethod
    def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame 데이터 타입 최적화"""
        optimized_df = df.copy()
        
        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype
            
            if col_type == 'object':
                # 문자열 컬럼을 category로 변환 (반복이 많은 경우)
                if optimized_df[col].nunique() / len(optimized_df) < 0.5:
                    optimized_df[col] = optimized_df[col].astype('category')
            
            elif col_type == 'float64':
                # float32로 다운캐스팅 (정밀도 허용 범위 내에서)
                if optimized_df[col].min() > -3.4e38 and optimized_df[col].max() < 3.4e38:
                    optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='float')
            
            elif col_type == 'int64':
                # int32 또는 더 작은 정수 타입으로 다운캐스팅
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='integer')
        
        return optimized_df
    
    @staticmethod
    def safe_numeric_conversion(series: pd.Series, errors: str = 'coerce') -> pd.Series:
        """안전한 숫자 타입 변환"""
        return pd.to_numeric(series, errors=errors)
    
    @staticmethod
    def safe_datetime_conversion(series: pd.Series, format: str = None) -> pd.Series:
        """안전한 날짜 타입 변환"""
        try:
            return pd.to_datetime(series, format=format)
        except ValueError as e:
            logger.warning(f"DateTime conversion failed: {e}")
            return pd.to_datetime(series, errors='coerce')
```

## 에러 처리 패턴

### 1. 계층화된 예외 처리

```python
from ai_canvas_sdk.exceptions import NodeException

class DataValidationError(NodeException):
    """데이터 검증 오류"""
    pass

class BusinessLogicError(NodeException):  
    """비즈니스 로직 오류"""
    pass

class ResourceError(NodeException):
    """리소스 관련 오류"""
    pass

class RobustNode(CustomNode):
    """견고한 에러 처리를 가진 노드"""
    
    def execute(self, inputs, parameters):
        try:
            return self._execute_safely(inputs, parameters)
        
        except DataValidationError as e:
            # 사용자가 수정 가능한 오류
            raise NodeException(
                message=f"데이터 검증 실패: {str(e)}",
                error_type="USER_INPUT_ERROR",
                suggestions=["데이터 형식을 확인하세요", "필수 컬럼이 있는지 확인하세요"]
            )
        
        except BusinessLogicError as e:
            # 로직 설정 문제
            raise NodeException(
                message=f"처리 로직 오류: {str(e)}",
                error_type="CONFIGURATION_ERROR", 
                suggestions=["파라미터 설정을 확인하세요"]
            )
        
        except ResourceError as e:
            # 시스템 리소스 문제 (재시도 가능)
            raise NodeException(
                message=f"리소스 부족: {str(e)}",
                error_type="RESOURCE_ERROR",
                retryable=True,
                suggestions=["데이터 크기를 줄이거나 나중에 다시 시도하세요"]
            )
        
        except Exception as e:
            # 예상치 못한 오류
            logger.error(f"Unexpected error in {self.__class__.__name__}: {str(e)}")
            raise NodeException(
                message="예상치 못한 오류가 발생했습니다",
                error_type="INTERNAL_ERROR",
                original_error=str(e)
            )
    
    def _execute_safely(self, inputs, parameters):
        """안전한 실행 로직"""
        
        # 입력 검증
        self._validate_inputs(inputs)
        
        # 리소스 확인
        self._check_resources(inputs)
        
        # 실제 처리
        return self._process_data(inputs, parameters)
    
    def _validate_inputs(self, inputs):
        """입력 검증"""
        df = inputs.get('data')
        if df is None or df.empty:
            raise DataValidationError("입력 데이터가 비어있습니다")
        
        if 'required_column' not in df.columns:
            raise DataValidationError("필수 컬럼 'required_column'이 없습니다")
    
    def _check_resources(self, inputs):
        """리소스 확인"""
        df = inputs['data']
        memory_usage_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        if memory_usage_mb > 1000:  # 1GB
            raise ResourceError(f"데이터가 너무 큽니다: {memory_usage_mb:.1f}MB")
```

### 2. 점진적 성능 저하 (Graceful Degradation)

```python
class AdaptiveNode(CustomNode):
    """상황에 따라 성능을 조정하는 노드"""
    
    def execute(self, inputs, parameters):
        df = inputs['data']
        
        # 데이터 크기에 따른 전략 선택
        if len(df) < 1000:
            return self._precise_processing(df, parameters)
        elif len(df) < 100000:
            return self._balanced_processing(df, parameters)
        else:
            return self._fast_processing(df, parameters)
    
    def _precise_processing(self, df, parameters):
        """정밀 처리 (소량 데이터)"""
        # 복잡한 알고리즘 사용
        result = df.apply(lambda x: self.complex_function(x), axis=1)
        return {'result': result, 'quality': 'high'}
    
    def _balanced_processing(self, df, parameters):
        """균형 처리 (중간 데이터)"""
        # 벡터화 연산 사용
        result = df.groupby('category').agg({'value': 'mean'})
        return {'result': result, 'quality': 'medium'}
    
    def _fast_processing(self, df, parameters):
        """고속 처리 (대량 데이터)"""
        # 샘플링 후 처리
        sample_df = df.sample(n=10000)
        result = sample_df.describe()
        return {'result': result, 'quality': 'low', 'note': 'Sampled result'}
```

## 테스트 가능한 노드 설계

### 1. 의존성 주입 패턴

```python
from abc import ABC, abstractmethod

class DataProcessor(ABC):
    """데이터 처리 인터페이스"""
    
    @abstractmethod
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

class StandardDataProcessor(DataProcessor):
    """표준 데이터 처리기"""
    
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        return data.groupby('category').mean()

class TestableNode(CustomNode):
    """테스트 가능한 노드"""
    
    def __init__(self, data_processor: DataProcessor = None):
        super().__init__()
        self.data_processor = data_processor or StandardDataProcessor()
    
    def run(self, inputs, parameters, ctx: NodeContext):
        df = inputs['data']
        
        # 주입된 프로세서 사용
        processed_data = self.data_processor.process(df)
        
        return {'processed_data': processed_data}

# 테스트용 모크 프로세서
class MockDataProcessor(DataProcessor):
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({'result': [1, 2, 3]})

# 테스트
def test_node():
    mock_processor = MockDataProcessor()
    node = TestableNode(data_processor=mock_processor)
    
    result = node.run({'data': pd.DataFrame()}, {}, NodeContext())
    assert 'processed_data' in result
```

### 2. 설정 가능한 노드

```python
@dataclass
class NodeConfig:
    """노드 설정"""
    max_memory_mb: int = 1000
    chunk_size: int = 10000
    timeout_seconds: int = 300
    enable_caching: bool = True
    debug_mode: bool = False

class ConfigurableNode(CustomNode):
    """설정 가능한 노드"""
    
    def __init__(self, config: NodeConfig = None):
        super().__init__()
        self.config = config or NodeConfig()
    
    def run(self, inputs, parameters, ctx: NodeContext):
        if self.config.debug_mode:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        
        df = inputs['data']
        
        # 설정에 따른 처리
        if self.config.enable_caching:
            result = self._process_with_cache(df, parameters)
        else:
            result = self._process_direct(df, parameters)
        
        return result
    
    def _process_with_cache(self, df, parameters):
        """캐시를 사용한 처리"""
        # 캐시 로직 구현
        return {'data': df}
    
    def _process_direct(self, df, parameters):
        """직접 처리"""
        return {'data': df}

# 사용 예시
config = NodeConfig(debug_mode=True, max_memory_mb=2000)
node = ConfigurableNode(config=config)
```

## 문서화 패턴

### 노드 문서 자동 생성

```python
class DocumentedNode(CustomNode):
    """문서화가 잘된 노드 예시"""
    
    @staticmethod
    def get_schema() -> NodeSchema:
        return NodeSchema(
            name="DocumentedNode",
            display_name="문서화된 노드",
            description="""
            이 노드는 입력 데이터를 처리하여 집계 결과를 반환합니다.
            
            주요 기능:
            - 데이터 필터링
            - 그룹별 집계
            - 통계 생성
            
            사용 사례:
            - 고객 데이터 분석
            - 판매 데이터 요약
            - 성과 지표 계산
            """,
            
            # 상세한 입력 문서
            inputs=[{
                "name": "source_data",
                "display_name": "원본 데이터",
                "type": PortType.DATAFRAME,
                "required": True,
                "description": """
                분석할 원본 데이터프레임입니다.
                
                필수 컬럼:
                - id: 고유 식별자 (정수)
                - category: 분류 (문자열)  
                - value: 수치 값 (실수)
                - date: 날짜 (datetime)
                
                예시:
                ```
                   id category  value       date
                0   1        A   10.5 2024-01-01
                1   2        B   20.3 2024-01-02
                ```
                """,
                "example": {
                    "columns": ["id", "category", "value", "date"],
                    "sample_rows": [
                        [1, "A", 10.5, "2024-01-01"],
                        [2, "B", 20.3, "2024-01-02"]
                    ]
                }
            }],
            
            # 상세한 출력 문서  
            outputs=[{
                "name": "aggregated_result",
                "display_name": "집계 결과", 
                "type": PortType.DATAFRAME,
                "description": """
                카테고리별로 집계된 결과입니다.
                
                출력 컬럼:
                - category: 분류명
                - count: 개수
                - mean_value: 평균값
                - sum_value: 총합
                """
            }]
        )
    
    def run(self, inputs, parameters, ctx: NodeContext):
        """
        노드 실행 함수
        
        Args:
            inputs: 입력 데이터 딕셔너리
                - source_data: 처리할 DataFrame
            parameters: 파라미터 딕셔너리
                - group_by: 그룹화 기준 컬럼명
        
        Returns:
            dict: 실행 결과
                - aggregated_result: 집계된 DataFrame
                - metadata: 처리 메타데이터
        
        Raises:
            ValueError: 입력 데이터가 유효하지 않은 경우
            KeyError: 필수 컬럼이 없는 경우
        
        Example:
            >>> inputs = {'source_data': df}
            >>> params = {'group_by': 'category'}
            >>> result = node.execute(inputs, params)
            >>> print(result['aggregated_result'])
        """
        # 실제 구현...
        pass

# 문서 자동 추출 유틸리티
def extract_node_documentation(node_class):
    """노드 문서 자동 추출"""
    schema = node_class.get_schema()
    execute_doc = node_class.run.__doc__
    
    documentation = {
        'name': schema.name,
        'description': schema.description,
        'inputs': schema.inputs,
        'outputs': schema.outputs,
        'parameters': schema.parameters,
        'execute_method': execute_doc
    }
    
    return documentation
```

---

이러한 **체계적인 개발 패턴**을 따르면 **유지보수 가능하고, 테스트 가능하며, 확장 가능한** 커스텀 노드를 개발할 수 있습니다.
