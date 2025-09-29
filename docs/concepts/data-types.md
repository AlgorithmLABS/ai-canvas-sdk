# 데이터 타입 및 직렬화

AI Canvas Custom Node SDK에서 지원하는 데이터 타입과 효율적인 직렬화 방법을 설명합니다.

## 지원 데이터 타입

### 기본 타입 (PortType Enum)

```python
from ai_canvas_sdk import PortType

class PortType(Enum):
    DATASET = "dataset"    # pandas DataFrame
    UNTRAINED = "untrainedModel"  # 학습되지 않은 ML 모델 (sklearn, pytorch 등)
    TRAINED = "trainedModel"   # 학습된 ML 모델
    TRANSFORMATION = "transformation" # 데이터셋 전처리
    DISPLAY = "display" # 포트 출력이 아닌데 노드에 표시할 데이터
    JSON = "json"              # 구조화된 데이터 (dict, list)
    
```

### 타입별 Python 매핑

| PortType | Python 타입 | 설명 | 직렬화 방식 |
|----------|-------------|------|------------|
| DATASET | `pandas.DataFrame` | 테이블 형태 데이터 | JSON/Parquet/Arrow |
| UNTRAINED | `dict[str, Any]` | 학습 전 모델/구성 파라미터 | JSON |
| TRAINED | `Any` (모델/아티팩트 핸들) | 학습된 모델 객체/포인터 | Pickle/Joblib |
| TRANSFORMATION | `str` 또는 `dict` | 변환기 정의/경로(spec/path) | JSON |
| DISPLAY | `dict`/`list`/`str`/`int`/`float`/`bool` | 노드 UI에 표시할 데이터(체이닝 없음) | JSON |
| JSON | `dict`, `list` | 일반 구조화 데이터 | JSON |

## 직렬화 메커니즘

### 1. DataFrame 직렬화

#### Parquet 방식 (기본값)
```python
# 장점: 최고 압축률, 스키마 보존
# 단점: 직렬화 시간 다소 소요

import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO

def serialize_dataframe_parquet(df: pd.DataFrame) -> bytes:
    """DataFrame을 Parquet 형식으로 직렬화"""
    buffer = BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, buffer, compression='snappy')
    return buffer.getvalue()

# 압축률 비교 (100만 행 데이터 기준)
original_size = df.memory_usage(deep=True).sum()  # 80MB
parquet_size = len(serialize_dataframe_parquet(df))  # 8MB (10배 압축!)
```

#### Arrow 방식 (고성능)
```python
# 장점: 높은 속도
# 단점: 압축률이 Parquet보다 낮음

import pyarrow as pa

def serialize_dataframe_arrow(df: pd.DataFrame) -> bytes:
    """DataFrame을 Arrow 형식으로 직렬화"""
    table = pa.Table.from_pandas(df)
    sink = pa.BufferOutputStream()
    with pa.ipc.RecordBatchStreamWriter(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()

# 성능 비교 (100만 행 기준)
parquet_time = 0.3  # 초
arrow_time = 0.05   # 초 (6배 빠름!)
```

#### 자동 전략 선택
```python
class DataFrameSerializer:
    @staticmethod
    def auto_serialize(df: pd.DataFrame) -> tuple[bytes, str]:
        """데이터 크기와 특성에 따라 최적 직렬화 방식 선택"""
        
        memory_usage_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        if memory_usage_mb < 1:
            # 작은 데이터는 JSON (호환성 우선)
            return df.to_json(orient='split').encode('utf-8'), "json"
        
        elif memory_usage_mb < 50:
            # 중간 데이터는 Parquet (압축 우선)
            return serialize_dataframe_parquet(df), "parquet"
        
        else:
            # 대용량 데이터는 Arrow (속도 우선)
            return serialize_dataframe_arrow(df), "arrow"
```

### 2. 모델 직렬화

```python
import pickle
import joblib
from typing import Any

class ModelSerializer:
    @staticmethod
    def serialize_model(model: Any, model_type: str = "auto") -> bytes:
        """ML 모델 직렬화"""
        
        if model_type == "auto":
            model_type = ModelSerializer._detect_model_type(model)
        
        buffer = BytesIO()
        
        if model_type in ["sklearn", "xgboost", "lightgbm"]:
            # scikit-learn 계열은 joblib 사용 (최적화됨)
            joblib.dump(model, buffer, compress=3)
        
        elif model_type in ["pytorch", "tensorflow"]:
            # 딥러닝 모델은 전용 방법 사용
            if hasattr(model, 'save'):
                model.save(buffer)  # TensorFlow
            elif hasattr(model, 'state_dict'):
                torch.save(model.state_dict(), buffer)  # PyTorch
            else:
                pickle.dump(model, buffer)  # 폴백
        
        else:
            # 일반적인 Python 객체
            pickle.dump(model, buffer, protocol=pickle.HIGHEST_PROTOCOL)
        
        return buffer.getvalue()
    
    @staticmethod
    def _detect_model_type(model: Any) -> str:
        """모델 타입 자동 감지"""
        module_name = model.__class__.__module__
        
        if 'sklearn' in module_name:
            return 'sklearn'
        elif 'xgboost' in module_name:
            return 'xgboost'
        elif 'lightgbm' in module_name:
            return 'lightgbm'
        elif 'torch' in module_name:
            return 'pytorch'
        elif 'tensorflow' in module_name:
            return 'tensorflow'
        else:
            return 'generic'
```


## 데이터 크기별 최적화 전략

### 크기 기준 가이드라인

```python
class DataSizeStrategy:
    """데이터 크기별 처리 전략"""
    
    SMALL_DATA_MB = 1      # 1MB 미만
    MEDIUM_DATA_MB = 10    # 10MB 미만
    LARGE_DATA_MB = 100    # 100MB 미만
    
    @staticmethod
    def get_strategy(data_size_mb: float) -> dict:
        """크기별 최적 전략 반환"""
        
        if data_size_mb < DataSizeStrategy.SMALL_DATA_MB:
            return {
                'serialization': 'json',
                'compression': 'none',
                'streaming': False,
                'chunk_size': None
            }
        
        elif data_size_mb < DataSizeStrategy.MEDIUM_DATA_MB:
            return {
                'serialization': 'parquet',
                'compression': 'snappy',
                'streaming': False,
                'chunk_size': None
            }
        
        elif data_size_mb < DataSizeStrategy.LARGE_DATA_MB:
            return {
                'serialization': 'arrow',
                'compression': 'lz4',
                'streaming': True,
                'chunk_size': 10000  # 행 단위
            }
        
        else:  # 100MB 이상
            return {
                'serialization': 'arrow',
                'compression': 'zstd',
                'streaming': True,
                'chunk_size': 5000   # 더 작은 청크
            }
```

### 실제 성능 벤치마크

```python
# 성능 테스트 결과 (참고용)
performance_benchmark = {
    "1MB_dataframe": {
        "json": {"size": "2.1MB", "serialize": "45ms", "deserialize": "67ms"},
        "parquet": {"size": "0.3MB", "serialize": "12ms", "deserialize": "8ms"},
        "arrow": {"size": "0.8MB", "serialize": "3ms", "deserialize": "2ms"}
    },
    
    "10MB_dataframe": {
        "json": {"size": "21MB", "serialize": "890ms", "deserialize": "1.2s"},
        "parquet": {"size": "2.1MB", "serialize": "120ms", "deserialize": "80ms"},
        "arrow": {"size": "7.5MB", "serialize": "35ms", "deserialize": "25ms"}
    },
    
    "100MB_dataframe": {
        "parquet": {"size": "12MB", "serialize": "1.2s", "deserialize": "800ms"},
        "arrow_streaming": {"size": "78MB", "serialize": "450ms", "deserialize": "380ms"}
    }
}
```

## 🔀 스트리밍 처리

### 대용량 DataFrame 스트리밍

```python
from typing import Iterator

class DataFrameStreamer:
    """대용량 DataFrame 스트리밍 처리"""
    
    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
    
    def stream_dataframe(self, df: pd.DataFrame) -> Iterator[bytes]:
        """DataFrame을 청크 단위로 스트리밍"""
        
        total_rows = len(df)
        for start_idx in range(0, total_rows, self.chunk_size):
            end_idx = min(start_idx + self.chunk_size, total_rows)
            chunk_df = df.iloc[start_idx:end_idx]
            
            # 청크 메타데이터 포함
            chunk_info = {
                'chunk_index': start_idx // self.chunk_size,
                'total_chunks': (total_rows + self.chunk_size - 1) // self.chunk_size,
                'start_row': start_idx,
                'end_row': end_idx,
                'total_rows': total_rows
            }
            
            # Arrow 직렬화
            table = pa.Table.from_pandas(chunk_df)
            sink = pa.BufferOutputStream()
            with pa.ipc.RecordBatchStreamWriter(sink, table.schema) as writer:
                writer.write_table(table)
            
            chunk_data = sink.getvalue().to_pybytes()
            
            yield self._create_chunk_message(chunk_data, chunk_info)
    
    def _create_chunk_message(self, data: bytes, info: dict) -> bytes:
        """청크 메시지 생성 (Protocol Buffer 형식)"""
        # 실제 구현에서는 protobuf 사용
        import json
        message = {
            'metadata': info,
            'data': data.hex()  # 예시용 hex 인코딩
        }
        return json.dumps(message).encode('utf-8')
```

### 스트리밍 수신 처리

```python
class StreamingReceiver:
    """스트리밍 데이터 수신 및 재조립"""
    
    def __init__(self):
        self.chunks = {}
        self.metadata = None
    
    def receive_chunk(self, chunk_message: bytes) -> bool:
        """청크 수신 및 저장"""
        import json
        
        message = json.loads(chunk_message.decode('utf-8'))
        metadata = message['metadata']
        data = bytes.fromhex(message['data'])
        
        if self.metadata is None:
            self.metadata = metadata
        
        chunk_index = metadata['chunk_index']
        self.chunks[chunk_index] = data
        
        # 모든 청크 수신 완료 확인
        total_chunks = metadata['total_chunks']
        return len(self.chunks) == total_chunks
    
    def reconstruct_dataframe(self) -> pd.DataFrame:
        """청크들을 재조립하여 원본 DataFrame 복원"""
        
        if not self.is_complete():
            raise ValueError("Not all chunks received")
        
        dataframes = []
        
        # 청크 순서대로 재조립
        for i in range(len(self.chunks)):
            chunk_data = self.chunks[i]
            
            # Arrow 역직렬화
            reader = pa.ipc.open_stream(BytesIO(chunk_data))
            table = reader.read_all()
            chunk_df = table.to_pandas()
            
            dataframes.append(chunk_df)
        
        return pd.concat(dataframes, ignore_index=True)
    
    def is_complete(self) -> bool:
        """모든 청크 수신 완료 확인"""
        if self.metadata is None:
            return False
        
        expected_chunks = self.metadata['total_chunks']
        return len(self.chunks) == expected_chunks
```

## 직렬화 설정

### SDK 설정 파일

```yaml
# ~/.ai-canvas/config.yaml
serialization:
  # DataFrame 기본 설정
  dataframe:
    format: "auto"        # auto, parquet, arrow, json
    compression: "snappy" # snappy, gzip, lz4, zstd, none
    chunk_size: 10000     # 스트리밍 청크 크기 (행 수)
  
  # 모델 직렬화 설정
  model:
    format: "auto"        # auto, pickle, joblib
    compression: 3        # joblib 압축 레벨 (0-9)
  
  # 이미지 설정
  image:
    format: "PNG"         # PNG, JPEG, WEBP
    quality: 95           # JPEG 품질 (1-100)
    optimize: true        # 최적화 여부
  
  # 스트리밍 설정
  streaming:
    threshold_mb: 10      # 스트리밍 시작 임계값
    max_chunk_size: 50000 # 최대 청크 크기
    buffer_size: 5        # 버퍼 청크 수
```

### 런타임 설정 변경

```python
from ai_canvas_sdk import SerializationConfig

class MyNode(CustomNode):
    def __init__(self):
        # 노드별 커스텀 설정
        self.config = SerializationConfig(
            dataframe_format="parquet",
            compression="lz4",
            streaming_threshold_mb=5
        )
    
    def run(self, inputs, parameters, ctx: NodeContext):
        # 임시 설정 변경
        with self.config.temporary_override(dataframe_format="arrow"):
            # 이 블록에서는 Arrow 형식 사용
            result = self.process_large_data(inputs['data'])
        
        return {'output': result}
```

## 디버깅 및 모니터링

### 직렬화 성능 모니터링

```python
import time
from contextlib import contextmanager

@contextmanager
def measure_serialization(operation: str):
    """직렬화 성능 측정 컨텍스트 매니저"""
    start_time = time.time()
    start_memory = get_memory_usage()
    
    try:
        yield
    finally:
        end_time = time.time()
        end_memory = get_memory_usage()
        
        print(f"{operation} 성능:")
        print(f"   시간: {(end_time - start_time) * 1000:.1f}ms")
        print(f"   메모리: {end_memory - start_memory:.1f}MB")

# 사용 예시
with measure_serialization("DataFrame Parquet 직렬화"):
    serialized_data = serialize_dataframe_parquet(large_df)
```

### 데이터 타입 검증

```python
def validate_data_type(data: Any, expected_type: PortType) -> bool:
    """데이터 타입 검증"""

    type_validators = {
        PortType.DATASET: lambda x: isinstance(x, pd.DataFrame),
        PortType.TRAINED: lambda x: (hasattr(x, 'predict') or hasattr(x, 'fit') or isinstance(x, (str, bytes, dict))),
        PortType.UNTRAINED: lambda x: isinstance(x, dict),
        PortType.TRANSFORMATION: lambda x: isinstance(x, (str, dict)),
        PortType.DISPLAY: lambda x: isinstance(x, (dict, list, str, int, float, bool)),
        PortType.JSON: lambda x: isinstance(x, (dict, list)),
    }

    validator = type_validators.get(expected_type)
    if validator is None:
        raise ValueError(f"Unknown type: {expected_type}")

    return validator(data)
```

## 메모리 효율성 팁

### 1. 메모리 사용량 최소화

```python
# 메모리 비효율적인 패턴
def bad_example(df: pd.DataFrame) -> pd.DataFrame:
    df_copy1 = df.copy()                    # 전체 복사
    df_copy2 = df_copy1.copy()              # 또 다른 복사
    result = df_copy2[df_copy2['value'] > 0] # 필터링
    return result

# 메모리 효율적인 패턴
def good_example(df: pd.DataFrame) -> pd.DataFrame:
    # 복사 없이 직접 필터링
    mask = df['value'] > 0
    result = df.loc[mask, ['col1', 'col2']]  # 필요한 컬럼만 선택
    return result
```

### 2. 청크 처리 패턴

```python
def process_large_dataframe_efficiently(df: pd.DataFrame, chunk_size: int = 10000):
    """메모리 효율적인 대용량 DataFrame 처리"""
    
    results = []
    
    for start in range(0, len(df), chunk_size):
        # 청크별 처리
        chunk = df.iloc[start:start + chunk_size]
        processed_chunk = process_chunk(chunk)
        results.append(processed_chunk)
        
        # 메모리 정리
        del chunk
    
    # 최종 결합
    return pd.concat(results, ignore_index=True)
```

---

이러한 데이터 타입과 직렬화 전략을 통해 **높은 성능**과 **효율적인 메모리 사용**을 달성할 수 있습니다.