# AI Canvas Custom Node SDK - 통합 제품 요구사항 문서 (PRD)

**문서 버전**: 1.0
**작성일**: 2025-09-17
**문서 소유자**: AI Canvas 백엔드팀
**최종 업데이트**: 2025-09-17

---

## 1. 배경과 목표

### 1.1 제품 비전
AI Canvas Custom Node SDK는 **개발자가 10분 내에 첫 번째 커스텀 노드를 생성하고 실행**할 수 있는 Python 기반 소프트웨어 개발 키트입니다. 강력한 성능과 엔터프라이즈급 보안을 제공하면서도, 직관적이고 개발자 친화적인 경험을 목표로 합니다.

### 1.2 핵심 목표
- **빠른 시작**: 설치부터 첫 노드 실행까지 < 10분
- **고성능**: 10만 행 DataFrame 처리 < 1.5초 (end-to-end)
- **확장성**: 대용량 데이터 스트리밍 및 분산 처리 지원
- **보안성**: mTLS, 샌드박스 실행, 리소스 제한
- **개발자 경험**: 데코레이터 기반 간편 개발 + 클래스 기반 고급 제어

### 1.3 Why Now?
- ML/데이터 파이프라인 확장 요구 급증
- 외부 파트너의 기능 제공 가속 필요
- 노코드/로우코드 플랫폼의 확장성 한계 극복
- 엔터프라이즈 고객의 보안 요구사항 증가

### 1.4 성공 정의
- **기술적 성공**: TTFHello < 10분, 성능 목표 달성, 99% 실행 성공률
- **비즈니스 성공**: B2B 계약 10건 이상

## 2. 사용자와 사용 시나리오

### 2.1 주요 페르소나

#### **Primary: 데이터 엔지니어/사이언티스트**
- **니즈**: 사내 데이터 처리 로직을 재사용 가능한 노드로 패키징
- **스킬**: Python 중급, pandas/numpy 능숙, ML 파이프라인 경험
- **페인 포인트**: 복잡한 설정, 성능 이슈, 디버깅 어려움

#### **Secondary: 파트너 개발자**
- **니즈**: 자체 모델/서비스를 AI Canvas에서 호출 가능한 노드로 제공
- **스킬**: Python 고급, 분산 시스템, API 개발
- **페인 포인트**: 보안 요구사항, 스케일링, 모니터링

#### **Tertiary: ML 엔지니어**
- **니즈**: 실험적 알고리즘을 프로덕션 워크플로우에 통합
- **스킬**: Python 고급, PyTorch/TensorFlow, MLOps
- **페인 포인트**: 버전 관리, A/B 테스트, 성능 최적화

### 2.2 핵심 사용 시나리오

#### 시나리오 1: 빠른 프로토타이핑
```
SDK 설치 → @simple_node 데코레이터 사용 → ai-canvas-sdk test로 즉시 확인
시간: < 10분, 복잡도: 매우 낮음
```

#### 시나리오 2: 엔터프라이즈 배포
```
CustomNode 클래스 상속 → 스키마 정의 → 단위 테스트 → 운영 체크리스트에 따른 프로덕션 배포
시간: 1-2일, 복잡도: 중간, 보안: 높음
```

#### 시나리오 3: 대용량 데이터 처리
```
스트리밍 노드 개발 → Parquet/Arrow 최적화 → 진행률 추적 → 분산 실행
데이터: 100만+ 행, 메모리: 효율적, 모니터링: 실시간
```

## 3. 범위 정의

### 3.1 In Scope ✅

#### **SDK Core**
- `CustomNode` 기본 클래스와 실행 런타임
- `@custom_node`, `@simple_node` 데코레이터 지원
- `NodeSchema`, `NodeContext` 핵심 인터페이스
- 타입 시스템 및 자동 검증

#### **통신 및 데이터**
- **gRPC**: 고성능 노드 실행 (mTLS 보안)
- **REST API**: 노드 관리 (등록, 조회, 삭제)
- **하이브리드 데이터 전송**: 직접 객체 + 파일 경로
- **스트리밍**: 대용량 데이터, 진행률, 로그

#### **개발자 도구**
- **CLI**: 현재 구현된 범위는 `test` 명령과 `--version` 옵션이며, 나머지 CLI 확장은 향후 범위로 둔다
- **IDE 통합**: VS Code Extension, 디버깅 지원
- **템플릿**: HelloWorld, DataFilter, ML Training, API Integration

#### **문서 및 예제**
- Getting Started (10분 완성)
- API Reference (완전한 명세)
- 고급 가이드 (성능, 보안, 최적화)
- FAQ 및 트러블슈팅

### 3.2 Out of Scope 
- Python 외 다국어 SDK (향후 Phase 2)
- 원격 오브젝트 스토리지 직접 통합 (공유 볼륨 우선)
- 실시간 모델 서빙 인프라 (별도 서비스)

### 3.3 Future Scope 
- AI Canvas 플랫폼 백엔드 자체 개선
- TypeScript/JavaScript SDK


## 4. 기능 요구사항

### 4.1 핵심 기능 (Must Have)

#### **FR1: 다양한 노드 정의 방식**

**간단한 함수 기반**:
```python
@simple_node
def filter_data(data: DataFrame, threshold: float = 0.5) -> DataFrame:
    """타입 힌트로 자동 스키마 생성"""
    return data[data.value > threshold]
```

**데코레이터 기반**:
```python
@custom_node(
    name="DataProcessor",
    category="processing",
    version="1.0.0",
    description="Advanced data processing node"
)
class DataProcessorNode(CustomNode):
    def get_schema(self) -> NodeSchema: ...
    def run(self, inputs, parameters, ctx) -> dict: ...
```

**클래스 상속 기반**:
```python
class AdvancedProcessorNode(CustomNode):
    def __init__(self):
        super().__init__()
        self.cache = {}

    def validate(self, inputs, parameters): ...
    def run(self, inputs, parameters, ctx): ...
    def cleanup(self): ...
```

#### **FR2: 강력한 타입 시스템과 검증**
```python
class NodeSchema:
    inputs = [
        InputPort("data", PortType.DATAFRAME, required=True),
        InputPort("config", PortType.JSON, default={}),
    ]
    outputs = [
        OutputPort("result", PortType.DATAFRAME),
        OutputPort("stats", PortType.JSON),
    ]
    parameters = [
        IntParameter("batch_size", min=1, max=1000, default=32),
        FloatParameter("threshold", min=0.0, max=1.0, default=0.5),
        SelectParameter("method", choices=["mean", "median"], default="mean"),
        SecretParameter("api_key", required=True),  # 암호화 저장
    ]
```

#### **FR3: 하이브리드 데이터 처리**

**자동 전략 선택**:
- 작은 데이터 (< 10MB): 직접 JSON/pickle 전송
- 큰 데이터 (≥ 10MB): Arrow/Parquet 파일 경로 교환
- 스트리밍: 청크 단위 처리 + 진행률 추적

```python
def run(self, inputs, parameters, ctx: NodeContext):
    # SDK가 자동으로 최적 방식 선택
    large_df = inputs['large_dataset']  # 자동 역직렬화

    # 진행률 추적
    ctx.progress(0.1, "데이터 로딩 완료")

    # 스트리밍 처리
    for chunk in ctx.stream_input('large_dataset', chunk_size=10000):
        processed = self.process_chunk(chunk)
        ctx.emit_partial('results', processed)
        ctx.progress(chunk.progress, f"처리 중... {chunk.index}/{chunk.total}")

    return {'final_result': final_data}
```

#### **FR4: 실행 제어 및 안정성**

**취소 처리**:
```python
def run(self, inputs, parameters, ctx):
    for i in range(1000):
        if ctx.is_cancelled():
            ctx.log_info("작업이 취소되었습니다")
            return {'status': 'cancelled'}

        # 장시간 작업
        process_batch(i)
```

**멱등성 지원**:
```python
@idempotent(key_fields=['input_hash', 'parameters'])
def run(self, inputs, parameters, ctx):
    # 동일한 입력에 대해 결과 캐시됨
    return expensive_computation(inputs)
```

#### **FR5: 기본 CLI**
```bash
# 개발 및 테스트
ai-canvas-sdk test my_node.py --validate-only
ai-canvas-sdk test my_node.py -i data.json -p '{"threshold": 0.5}' -o output.json -v
ai-canvas-sdk --version
```

### 4.2 고급 기능 (Should Have)

#### **FR6: 통합 테스팅 프레임워크**
```python
from ai_canvas_sdk.testing import NodeTester, MockContext

def test_data_filter_node():
    tester = NodeTester(DataFilterNode)

    # Mock 데이터 생성
    test_data = tester.create_sample_dataframe(rows=1000)

    # 실행 및 검증
    result = tester.run(
        inputs={'data': test_data},
        parameters={'threshold': 0.5}
    )

    assert len(result['filtered_data']) < len(test_data)
    assert 'stats' in result
```

#### **FR7: 성능 프로파일링**
```python
@profile_performance
def run(self, inputs, parameters, ctx):
    # 자동 성능 측정
    return process_data(inputs)

# 결과: 실행 시간, 메모리 사용량, I/O 통계
```

#### **FR8: 플러그인 시스템**
```python
@use_plugin('cache')
@use_plugin('metrics')
class CachedNode(CustomNode):
    def run(self, inputs, parameters, ctx):
        # 캐시 및 메트릭 자동 적용
        return results
```

## 5. 비기능 요구사항

### 5.1 성능 요구사항

| 메트릭 | 목표 | 측정 방법 |
|--------|------|-----------|
| **TTFHello** | < 10분 | 설치부터 첫 노드 실행까지 |
| **직렬화 성능** | < 400ms | 10만 행 DataFrame 변환 |
| **End-to-End** | < 1.5초 | 로컬 실행 전체 파이프라인 |
| **메모리 효율** | < 2x 원본 | 최대 메모리 사용량 |
| **동시 실행** | 100개 노드 | 리소스 경합 없이 |

### 5.2 안정성 요구사항

- **실행 성공률**: > 99%
- **취소 시 정리**: 100% (임시 파일, 메모리 누수 없음)
- **재시작 성공률**: > 99% (오류 복구 후)
- **데이터 무결성**: 원자적 연산 보장

### 5.3 보안 요구사항

#### **통신 보안**
- 모든 gRPC 호출 mTLS 암호화
- 인증서 자동 로테이션
- API 키 암호화 저장

#### **실행 보안**
- 샌드박스 실행 환경 (컨테이너)
- 리소스 제한 (CPU, 메모리, 디스크)
- 네트워크 접근 제어
- 코드 서명 및 검증

#### **데이터 보안**
- 공유 볼륨 최소 권한 (770)
- 개인정보 마스킹 옵션
- 감사 로그 기록

### 5.4 호환성 요구사항

- **Python**: 3.8+ (권장 3.10+)
- **OS**: Linux, macOS, Windows
- **의존성**: 최소화 (core: pandas, numpy, grpcio)
- **AI Canvas**: 플랫폼 버전 2.0+

## 6. 아키텍처 및 기술 설계

### 6.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Canvas Frontend                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                AI Canvas Backend (FastAPI)                  │
│  ├─ REST API (노드 관리)                                    │
│  ├─ WebSocket (실시간 업데이트)                              │
│  └─ Celery Task Queue                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ Task Dispatch
┌─────────────────────▼───────────────────────────────────────┐
│                    DAG Worker                               │
│  ├─ 워크플로우 오케스트레이션                                │
│  ├─ 노드 실행 관리                                          │
│  └─ 결과 수집 및 전달                                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ gRPC (mTLS)
┌─────────────────────▼───────────────────────────────────────┐
│                Custom Node Server                           │
│  ├─ ExecuteNode(req) → res                                  │
│  ├─ ExecuteNodeStream(req) → stream progress                │
│  ├─ RegisterNode(def) → result                              │
│  └─ HealthCheck() → status                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ SDK Interface
┌─────────────────────▼───────────────────────────────────────┐
│                  Custom Node (SDK)                          │
│  ├─ @simple_node / @custom_node                             │
│  ├─ CustomNode 클래스                                       │
│  ├─ 비즈니스 로직 구현                                       │
│  └─ 자동 데이터 처리                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   공유 데이터 계층                           │
│  ├─ /data/{canvas_id}/{node_id}/{run_id}/                   │
│  ├─ Arrow/Parquet 파일 (대용량)                              │
│  ├─ JSON 메타데이터 (소량)                                   │
│  └─ 임시 파일 원자적 처리                                    │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 gRPC 서비스 명세

```protobuf
syntax = "proto3";

service CustomNodeExecutor {
  // 단일 노드 실행
  rpc ExecuteNode(NodeRequest) returns (NodeResponse);

  // 스트리밍 실행 (대용량 데이터 + 진행률)
  rpc ExecuteNodeStream(NodeRequest) returns (stream NodeProgress);

  // 노드 등록 및 검증
  rpc RegisterNode(NodeDefinition) returns (RegistrationResult);

  // 헬스체크
  rpc HealthCheck(HealthRequest) returns (HealthResponse);

  // 노드 취소
  rpc CancelExecution(CancelRequest) returns (CancelResponse);
}

message NodeRequest {
  string execution_id = 1;
  string node_id = 2;
  string node_type = 3;

  // 하이브리드 데이터 전송
  repeated PortData direct_inputs = 4;    // 작은 데이터
  repeated FileReference file_inputs = 5; // 큰 데이터 파일 경로

  map<string, Value> parameters = 6;
  ExecutionOptions options = 7;
}

message NodeProgress {
  string execution_id = 1;
  float progress = 2;           // 0.0 - 1.0
  string message = 3;
  LogEntry log_entry = 4;
  PartialResult partial = 5;
  ExecutionMetrics metrics = 6;
}
```

### 6.3 데이터 직렬화 전략

#### **자동 전략 선택**
```python
class DataStrategy:
    @staticmethod
    def choose_strategy(data_size_mb: float) -> str:
        if data_size_mb < 1:
            return "json"      # 즉시 전송
        elif data_size_mb < 10:
            return "pickle"    # 압축 전송
        else:
            return "parquet"   # 파일 경로 교환
```

#### **파일 네임스페이스**
```
/shared_volume/
├── data/
│   ├── {canvas_id}/
│   │   ├── {node_id}/
│   │   │   ├── {run_id}/
│   │   │   │   ├── inputs/
│   │   │   │   │   ├── port1.parquet
│   │   │   │   │   └── port2.arrow
│   │   │   │   ├── outputs/
│   │   │   │   │   └── result.parquet
│   │   │   │   └── temp/
│   │   │   │       └── processing.tmp
```

### 6.4 실행 제어 시스템

#### **상태 전이**
```
PENDING → RUNNING → SUCCESS
    ↓         ↓         ↓
    ↓         ▼         ▼
    └─► FAILED ← TIMEOUT
           ↓
        RETRY
```

#### **취소 및 정리**
```python
class ExecutionController:
    def cancel_execution(self, execution_id: str):
        # 1. 취소 신호 전송
        self.send_cancel_signal(execution_id)

        # 2. 임시 파일 정리
        self.cleanup_temp_files(execution_id)

        # 3. 리소스 해제
        self.release_resources(execution_id)

        # 4. 상태 업데이트
        self.update_status(execution_id, "CANCELLED")
```

## 7. SDK 인터페이스 설계

### 7.1 핵심 클래스

#### **CustomNode 기본 클래스**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class CustomNode(ABC):
    """커스텀 노드 기본 클래스"""

    def __init__(self):
        self._execution_context: Optional[NodeContext] = None

    @abstractmethod
    def get_schema(self) -> NodeSchema:
        """노드 스키마 정의"""
        pass

    @abstractmethod
    def run(self, inputs: Dict[str, Any], parameters: Dict[str, Any],
            ctx: NodeContext) -> Dict[str, Any]:
        """노드 실행 로직"""
        pass

    def validate(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        """입력 검증 (선택적)"""
        pass

    def cleanup(self) -> None:
        """리소스 정리 (선택적)"""
        pass
```

#### **NodeContext 실행 컨텍스트**
```python
class NodeContext:
    """노드 실행 컨텍스트"""

    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self._cancelled = False
        self._temp_files = []

    # 진행률 및 로깅
    def progress(self, percentage: float, message: str = None):
        """진행률 업데이트 (0.0 - 1.0)"""

    def log_info(self, message: str, extra: Dict = None):
        """정보 로그 기록"""

    def log_warning(self, message: str, extra: Dict = None):
        """경고 로그 기록"""

    def log_error(self, message: str, extra: Dict = None):
        """에러 로그 기록"""

    # 실행 제어
    def is_cancelled(self) -> bool:
        """취소 여부 확인"""
        return self._cancelled

    def emit_partial(self, port_name: str, data: Any):
        """부분 결과 전송 (스트리밍)"""

    # 리소스 관리
    def get_temp_file(self, suffix: str = ".tmp") -> str:
        """임시 파일 경로 생성"""
        temp_path = f"/tmp/{self.execution_id}_{uuid4()}{suffix}"
        self._temp_files.append(temp_path)
        return temp_path

    def register_cleanup(self, callback: Callable):
        """정리 콜백 등록"""
```

### 7.2 데코레이터 시스템

#### **간단한 함수 기반**
```python
@simple_node
def add_numbers(a: float, b: float) -> float:
    """두 숫자를 더합니다"""
    return a + b

# 자동 변환됨:
# - 타입 힌트 → 포트 정의
# - docstring → 설명
# - 함수명 → 노드명
```

#### **고급 데코레이터**
```python
@custom_node(
    name="DataAnalyzer",
    display_name="데이터 분석기",
    category="analytics",
    version="1.2.0",
    description="고급 데이터 분석 및 시각화",
    tags=["ml", "stats", "visualization"],
    timeout=300,
    memory_limit="2GB"
)
class DataAnalyzerNode(CustomNode):
    # 스키마는 클래스 내부에서 정의
    pass
```

### 7.3 파라미터 타입 시스템

```python
class NodeSchema:
    inputs = [
        InputPort(
            name="dataset",
            type=PortType.DATAFRAME,
            required=True,
            description="분석할 데이터셋"
        ),
        InputPort(
            name="config",
            type=PortType.JSON,
            required=False,
            default={},
            description="추가 설정"
        )
    ]

    outputs = [
        OutputPort(
            name="analysis_result",
            type=PortType.DATAFRAME,
            description="분석 결과"
        ),
        OutputPort(
            name="summary_stats",
            type=PortType.JSON,
            description="요약 통계"
        ),
        OutputPort(
            name="visualization",
            type=PortType.DISPLAY,  # 차트/그래프
            description="시각화 결과"
        )
    ]

    parameters = [
        # 숫자 파라미터
        IntParameter(
            name="sample_size",
            display_name="샘플 크기",
            min=100,
            max=1000000,
            default=10000,
            description="분석에 사용할 샘플 데이터 크기"
        ),

        FloatParameter(
            name="confidence_level",
            display_name="신뢰도",
            min=0.8,
            max=0.99,
            default=0.95,
            step=0.01,
            description="통계적 신뢰 수준"
        ),

        # 선택 파라미터
        SelectParameter(
            name="analysis_method",
            display_name="분석 방법",
            choices=[
                {"label": "기본 통계", "value": "basic"},
                {"label": "고급 분석", "value": "advanced"},
                {"label": "ML 분석", "value": "ml"}
            ],
            default="basic",
            description="사용할 분석 방법"
        ),

        # 다중 선택
        MultiSelectParameter(
            name="metrics",
            display_name="계산할 메트릭",
            choices=[
                "mean", "median", "std", "correlation", "skewness"
            ],
            default=["mean", "std"],
            description="계산할 통계 메트릭"
        ),

        # 불린 파라미터
        BoolParameter(
            name="enable_visualization",
            display_name="시각화 생성",
            default=True,
            description="분석 결과 차트 생성 여부"
        ),

        # 문자열 파라미터
        StringParameter(
            name="output_format",
            display_name="출력 형식",
            default="html",
            pattern=r"^(html|pdf|png)$",
            description="결과 출력 형식"
        ),

        # 비밀 파라미터
        SecretParameter(
            name="api_key",
            display_name="API 키",
            required=True,
            description="외부 서비스 API 키 (암호화 저장)"
        ),

        # 파일 파라미터
        FileParameter(
            name="config_file",
            display_name="설정 파일",
            accept=[".json", ".yaml", ".csv"],
            max_size="10MB",
            description="추가 설정 파일"
        )
    ]
```

### 7.4 고급 기능

#### **스트리밍 처리**
```python
class StreamingNode(CustomNode):
    def run(self, inputs, parameters, ctx):
        large_dataset = inputs['large_dataset']

        # 자동 청크 처리
        total_chunks = len(large_dataset) // 10000

        results = []
        for i, chunk in enumerate(ctx.stream_input('large_dataset', chunk_size=10000)):
            # 진행률 업데이트
            progress = (i + 1) / total_chunks
            ctx.progress(progress, f"처리 중... {i+1}/{total_chunks}")

            # 청크 처리
            processed = self.process_chunk(chunk)
            results.append(processed)

            # 부분 결과 전송 (선택적)
            ctx.emit_partial('intermediate_results', processed.describe())

        # 최종 결과
        final_result = pd.concat(results)
        return {'processed_data': final_result}
```

#### **에러 처리 및 복구**
```python
class RobustNode(CustomNode):
    def run(self, inputs, parameters, ctx):
        try:
            return self.main_logic(inputs, parameters, ctx)

        except DataValidationError as e:
            ctx.log_error(f"데이터 검증 실패: {e}")
            raise NodeExecutionError(
                message="입력 데이터가 유효하지 않습니다",
                error_type="VALIDATION_ERROR",
                suggestions=["데이터 형식을 확인하세요", "필수 컬럼을 확인하세요"]
            )

        except ResourceError as e:
            ctx.log_warning(f"리소스 부족: {e}")
            # 자동 재시도 가능
            raise RetryableNodeError(
                message="리소스가 부족합니다",
                retry_after=30
            )

        except Exception as e:
            ctx.log_error(f"예상치 못한 오류: {e}")
            raise NodeExecutionError(
                message="내부 오류가 발생했습니다",
                error_type="INTERNAL_ERROR"
            )
```

## 8. CLI 명세

### 8.1 프로젝트 관리

- 프로젝트 초기화: 표준화된 프로젝트 골격을 생성하고, 템플릿 선택을 통해 서로 다른 시작 구성을 제공한다.
- 템플릿 관리: 템플릿 목록 조회와 상세 확인 기능으로 개발자가 적합한 시작점을 빠르게 선택할 수 있도록 지원한다.

### 8.2 개발 및 테스트

- 노드 검증: 노드 정의와 스키마를 문서화된 절차에 따라 검증한다.
- 로컬 실행: 실행 시에는 입력 데이터, 파라미터, 출력 경로, 상세 로그 옵션을 조합해 사용한다.
- 단위 테스트: 구현된 `test` 명령으로 검증 전용 실행과 입출력 기반 실행을 지원한다.

```bash
# 단위 테스트
ai-canvas-sdk test my_node.py --validate-only
ai-canvas-sdk test my_node.py -i input.json -p '{"threshold": 0.8}' -o output.json -v

# 버전 확인
ai-canvas-sdk --version
```

### 8.3 패키징 및 배포

- 패키징: 패키징과 배포 절차는 릴리스 체크리스트와 운영 가이드를 따른다.
- 등록(개발 환경): 배포 대상 등록은 플랫폼 운영 절차에 따라 수행한다.
- 배포(프로덕션): 배포 승인 및 게시 단계는 운영 정책에 맞춰 관리한다.

### 8.4 유틸리티

```bash
# 버전 및 환경 정보
ai-canvas-sdk --version
```

- 문서화: 문서 생성과 로컬 문서 서버는 SDK API와 노드 예제를 자동으로 정리해 개발자 온보딩과 참조를 돕는다.
- 로그 및 디버깅: 로그 조회와 실시간 추적 기능은 노드 실행 상태와 디버깅 흐름을 운영자가 확인할 수 있게 해준다.

## 9. 테스트 전략 및 수용 기준

### 9.1 테스트 피라미드

#### **단위 테스트 (60%)**
- 스키마 검증 및 타입 체크
- 데이터 직렬화/역직렬화
- 노드 실행 로직
- 에러 처리 시나리오

#### **통합 테스트 (30%)**
- gRPC 통신 (Execute/Stream)
- 파일 I/O 및 공유 볼륨
- 현재 구현된 CLI 흐름(`test`, `--version`) 검증
- 실행 제어 (취소/타임아웃)

#### **E2E 테스트 (10%)**
- 전체 워크플로우 (개발→배포→실행)
- 성능 벤치마크
- 보안 테스트
- 사용자 시나리오

### 9.2 성능 테스트

```python
class PerformanceTests:
    def test_serialization_performance(self):
        """직렬화 성능 테스트"""
        df = create_test_dataframe(rows=100000)

        # Parquet 직렬화
        start_time = time.time()
        serialized = serialize_dataframe(df, format='parquet')
        parquet_time = time.time() - start_time

        assert parquet_time < 0.4  # 400ms 이내
        assert len(serialized) < len(df) * 0.5  # 50% 압축

    def test_end_to_end_performance(self):
        """전체 실행 성능 테스트"""
        node = create_test_node()
        large_input = create_test_data(rows=100000)

        start_time = time.time()
        result = execute_node_locally(node, large_input)
        total_time = time.time() - start_time

        assert total_time < 1.5  # 1.5초 이내
        assert result['status'] == 'success'
```

### 9.3 수용 기준 (Acceptance Criteria)

#### **A1: 빠른 시작 (TTFHello < 10분)**
```
✅ SDK 설치 성공 (< 2분)
✅ HelloWorld 노드 생성 (< 3분)
✅ 로컬 실행 성공 (< 2분)
✅ 결과 확인 (< 1분)
✅ 문서 따라하기만으로 완료 가능
```

#### **A2: 데이터 처리 성능**
```
✅ 10만 행 DataFrame 처리 < 1.5초
✅ Parquet 직렬화 < 400ms
✅ 메모리 사용량 < 2x 원본 크기
✅ 스트리밍 진행률 실시간 업데이트
```

#### **A3: 실행 제어 안정성**
```
✅ 취소 신호 수신 시 < 5초 내 중단
✅ 임시 파일 100% 정리
✅ 메모리 누수 없음
✅ 타임아웃 후 자동 리소스 해제
```

#### **A4: CLI 기능 완성도**
```
✅ 현재 구현된 CLI 명령어(`test`, `--version`) 정상 동작
✅ 에러 메시지 명확성
✅ 진행률 표시 정확성
✅ 결과 출력 형식 일관성
```

#### **A5: 프로덕션 배포 성공**
```
✅ 패키징 성공률 > 98%
✅ 등록 프로세스 완료
✅ 캔버스에서 노드 실행 가능
✅ 로그 및 모니터링 정상 작동
```

## 10. 마일스톤 및 일정

### 10.1 8주 개발 계획

#### **Week 1: Foundation & Architecture**
**목표**: 기반 설계 및 환경 구축

**Deliverables**:
- [ ] 상세 기술 설계서 완성
- [ ] gRPC Proto 스키마 정의
- [ ] 개발 환경 셋업 (CI/CD)
- [ ] 보안 정책 문서화 (mTLS, 권한)
- [ ] 프로젝트 구조 및 패키지 초기화

**Risk**: 기술 스택 선택 지연, 보안 요구사항 복잡도

#### **Week 2: Core SDK Framework**
**목표**: SDK 핵심 프레임워크 구현

**Deliverables**:
- [ ] `CustomNode` 기본 클래스 구현
- [ ] `NodeSchema` 타입 시스템 구현
- [ ] `NodeContext` 실행 컨텍스트 구현
- [ ] 기본 데코레이터 (`@simple_node`, `@custom_node`)
- [ ] 스키마 검증 엔진

**Risk**: 타입 시스템 복잡도, 메타클래스 이슈

#### **Week 3: Data Handling & Serialization**
**목표**: 데이터 처리 및 직렬화 시스템 구현

**Deliverables**:
- [ ] 하이브리드 데이터 전송 시스템
- [ ] Arrow/Parquet 직렬화 엔진
- [ ] 자동 전략 선택 알고리즘
- [ ] 파일 네임스페이스 관리
- [ ] 원자적 파일 연산 (temp → final rename)

**Risk**: 대용량 데이터 성능, 동시성 이슈

#### **Week 4: gRPC Communication**
**목표**: gRPC 통신 및 스트리밍 구현

**Deliverables**:
- [ ] gRPC 서비스 구현 (Execute, Stream, Register, Health)
- [ ] mTLS 인증 시스템
- [ ] 스트리밍 진행률 및 로그 전송
- [ ] 취소 및 타임아웃 처리
- [ ] 에러 처리 및 재시도 로직

**Risk**: gRPC 스트리밍 복잡도, mTLS 설정

#### **Week 5: Current CLI Surface & Developer Experience**
**목표**: CLI 도구 및 개발자 경험 구현

**Deliverables**:
- [ ] 기본 CLI 범위 정리 및 `test`/`--version` 문서화
- [ ] CLI 향후 확장 명세 정리
- [ ] 에러 메시지 및 제안사항 시스템

**Risk**: CLI UX 복잡도, 크로스 플랫폼 호환성

#### **Week 6: Testing Framework & Examples**
**목표**: 테스팅 프레임워크 및 예제 노드 구현

**Deliverables**:
- [ ] `NodeTester` 테스팅 프레임워크
- [ ] Mock 시스템 (`MockContext`, 샘플 데이터 생성)
- [ ] 예제 노드 구현 (HelloWorld, DataFilter, ML Training, API Integration, Streaming)
- [ ] 단위 테스트 스위트 (커버리지 > 80%)
- [ ] 통합 테스트 시나리오

**Risk**: 테스트 환경 복잡도, 모킹 시스템 한계

#### **Week 7: Performance Optimization & Security**
**목표**: 성능 최적화 및 보안 강화

**Deliverables**:
- [ ] 성능 벤치마크 및 최적화 (목표: TTFHello < 10분, 처리 성능 < 1.5초)
- [ ] 메모리 최적화 및 누수 방지
- [ ] 보안 스캔 및 취약점 수정
- [ ] 리소스 제한 및 샌드박스 강화
- [ ] 로드 테스트 (동시 100개 노드)

**Risk**: 성능 목표 달성 실패, 보안 취약점 발견

#### **Week 8: Documentation & Release**
**목표**: 문서화 및 릴리스 준비

**Deliverables**:
- [ ] 완전한 문서 (Getting Started, API Reference, 고급 가이드, FAQ)
- [ ] 릴리스 노트 및 변경 로그
- [ ] 배포 파이프라인 구축
- [ ] 사용자 수용 테스트 (UAT)
- [ ] 프로덕션 배포 및 모니터링 셋업

**Risk**: 문서 품질, 릴리스 안정성

### 10.2 위험 요소 및 완화 방안

| 위험 | 확률 | 영향 | 완화 방안 |
|------|------|------|-----------|
| **PyArrow 빌드 실패** | 중간 | 높음 | 사전 컴파일된 바이너리, 대안 설치 가이드 |
| **gRPC 성능 이슈** | 낮음 | 높음 | 벤치마크 주기적 실행, HTTP/2 최적화 |
| **대용량 메모리 문제** | 높음 | 중간 | 청크 처리, 스트리밍, 사전 알림 |
| **보안 취약점** | 낮음 | 높음 | 보안 스캔 자동화, 외부 감사 |
| **개발 일정 지연** | 중간 | 중간 | 버퍼 시간, 핵심 기능 우선순위 |

## 11. 성공 지표 (KPI)

### 11.1 기술 지표

| 메트릭 | 목표 | 측정 방법 | 측정 주기 |
|--------|------|-----------|-----------|
| **TTFHello** | < 10분 | 사용자 테스트 | 매 릴리스 |
| **실행 성공률** | > 99% | 로그 분석 | 일간 |
| **성능** | < 1.5초 | 자동 벤치마크 | 일간 |
| **메모리 효율** | < 2x 원본 | 프로파일링 | 주간 |
| **취소 정리율** | 100% | 단위 테스트 | 빌드마다 |

### 11.2 비즈니스 지표

| 메트릭 | 1개월 목표 | 3개월 목표 | 6개월 목표 |
|--------|------------|------------|------------|
| **월간 활성 개발자** | 50명 | 200명 | 1,000명 |
| **생성된 노드 수** | 100개 | 1,000개 | 5,000개 |
| **노드 실행 횟수** | 1만회 | 10만회 | 100만회 |
| **커뮤니티 기여도** | 5개 PR | 20개 PR | 100개 PR |

### 11.3 품질 지표

| 메트릭 | 목표 | 측정 방법 |
|--------|------|-----------|
| **NPS (Net Promoter Score)** | > 50 | 분기별 설문 |
| **문서 만족도** | > 4.0/5.0 | 문서 피드백 |
| **지원 응답 시간** | < 24시간 | 헬프데스크 |
| **버그 수정 시간** | < 7일 | 이슈 트래커 |
| **SDK 다운로드 성공률** | > 95% | 패키지 매니저 |

## 12. 리스크 관리 및 대응

### 12.1 기술적 리스크

#### **HIGH: 의존성 설치 실패**
- **시나리오**: PyArrow, gRPC 컴파일 실패 (특히 ARM, 오래된 시스템)
- **영향**: 설치 불가, 첫 경험 실패
- **완화 방안**:
  - 사전 컴파일된 wheel 제공
  - Docker 기반 개발 환경 옵션
  - 의존성 없는 경량 모드 제공
  - 상세한 설치 트러블슈팅 가이드

#### **MEDIUM: 성능 목표 미달성**
- **시나리오**: 대용량 데이터 처리 시 1.5초 초과
- **영향**: 사용자 경험 저하, 채택률 감소
- **완화 방안**:
  - 조기 벤치마킹 및 지속적 모니터링
  - 프로파일링 도구 내장
  - 청크 크기 자동 최적화
  - 병렬 처리 옵션 제공

#### **MEDIUM: 메모리 누수 및 리소스 문제**
- **시나리오**: 장시간 실행 시 메모리 누수, 임시 파일 미정리
- **영향**: 시스템 안정성 저하
- **완화 방안**:
  - 자동 가비지 컬렉션 강화
  - Context manager 패턴 강제
  - 리소스 모니터링 및 알림
  - 정기적 메모리 테스트

### 12.2 보안 리스크

#### **HIGH: 악성 코드 실행**
- **시나리오**: 사용자 노드에서 시스템 공격
- **영향**: 보안 침해, 데이터 유출
- **완화 방안**:
  - 컨테이너 샌드박스 강제
  - 네트워크 접근 제한
  - 파일 시스템 권한 최소화
  - 코드 정적 분석 도구

#### **MEDIUM: 인증서 관리 실패**
- **시나리오**: mTLS 인증서 만료, 로테이션 실패
- **영향**: 통신 불가, 서비스 중단
- **완화 방안**:
  - 자동 인증서 갱신
  - 만료 전 알림 시스템
  - Fallback 인증 방식
  - 인증서 모니터링 대시보드

### 12.3 비즈니스 리스크

#### **HIGH: 개발자 채택률 저조**
- **시나리오**: 복잡한 설정, 낮은 접근성으로 사용자 확보 실패
- **영향**: 비즈니스 목표 미달성
- **완화 방안**:
  - 철저한 UX 테스트
  - 단계별 온보딩 가이드
  - 커뮤니티 지원 프로그램
  - 인센티브 프로그램 (해커톤, 컨테스트)

#### **MEDIUM: 경쟁 솔루션 등장**
- **시나리오**: 유사한 SDK나 플랫폼 등장
- **영향**: 시장 점유율 감소
- **완화 방안**:
  - 차별화된 기능 (성능, 보안)
  - 에코시스템 구축
  - 파트너십 강화
  - 지속적 혁신

## 13. 종속성 및 전제 조건

### 13.1 기술적 종속성

#### **필수 종속성**
- **AI Canvas Backend**: 노드 등록 API, 실행 큐
- **gRPC Server**: 커스텀 노드 실행 엔드포인트
- **공유 볼륨**: 대용량 데이터 교환 스토리지
- **MongoDB**: 노드 메타데이터 저장
- **Redis**: 캐시 및 세션 관리

#### **선택적 종속성**
- **Container Registry**: 노드 이미지 저장
- **Monitoring System**: 성능 메트릭 수집
- **Log Aggregation**: 구조화된 로그 분석

### 13.2 인프라 전제 조건

#### **네트워크**
- gRPC 포트 개방 (기본: 50051)
- mTLS 인증서 인프라
- DNS 해상도 및 로드 밸런싱

#### **스토리지**
- 공유 볼륨 마운트 (최소 100GB)
- 백업 및 스냅샷 정책
- 권한 관리 (UID/GID 매핑)

#### **보안**
- 인증서 발급 및 관리 시스템
- 컨테이너 런타임 보안 정책
- 네트워크 분할 및 방화벽

### 13.3 조직적 전제 조건

#### **개발팀**
- Python 고급 개발자 2-3명
- DevOps 엔지니어 1명
- 보안 전문가 1명 (파트타임)
- Technical Writer 1명

#### **승인 프로세스**
- 보안 검토 및 승인
- 성능 테스트 통과
- 문서 품질 검증
- 법적 검토 (라이센스, 규정 준수)

## 14. 오픈 이슈 및 결정 사항

### 14.1 미결정 사항 🤔

#### **기술적 결정**
1. **PortType 세분화**
   - 현재: DATAFRAME, DATASET, DISPLAY
   - 고려사항: IMAGE, VIDEO, AUDIO, MODEL 추가 여부
   - 결정 필요: Week 2 말까지

2. **멱등성 키 범위**
   - 옵션 A: 입력 데이터 해시 포함 (정확하지만 느림)
   - 옵션 B: 파라미터만 포함 (빠르지만 부정확)
   - 결정 필요: Week 3 중

3. **SDK 배포 채널**
   - 옵션 A: PyPI 공개 (접근성 좋음)
   - 옵션 B: 내부 레지스트리 (보안 좋음)
   - 옵션 C: 하이브리드 (공개 + 프라이빗)
   - 결정 필요: Week 7

#### **정책적 결정**
4. **노드 인증 정책**
   - 자동 승인 vs 수동 검토
   - 보안 스캔 기준
   - 커뮤니티 노드 품질 관리

5. **라이센스 정책**
   - SDK 라이센스 (MIT vs Apache 2.0)
   - 커뮤니티 노드 라이센스 요구사항
   - 상업적 이용 정책

### 14.2 제약 사항 및 한계 ⚠️

#### **기술적 제약**
- **Python 버전**: 3.8+ (3.7 미만 지원 안함)
- **메모리 제한**: 노드당 최대 4GB
- **실행 시간**: 최대 30분 (타임아웃)
- **파일 크기**: 단일 파일 최대 1GB
- **동시 실행**: 사용자당 최대 10개 노드

#### **보안 제약**
- **네트워크 접근**: 화이트리스트 기반만 허용
- **파일 시스템**: 지정된 디렉토리 외 접근 금지
- **시스템 호출**: 제한된 syscall만 허용
- **리소스 접근**: CPU, 메모리, 디스크 I/O 제한

#### **비즈니스 제약**
- **개발 예산**: 8주, 4명 개발자
- **인프라 비용**: 월 $10K 이내
- **성능 목표**: 하드웨어 업그레이드 없이 달성
- **규정 준수**: GDPR, SOC2 요구사항 충족

## 15. 릴리스 및 배포 전략

### 15.1 버전 관리

#### **Semantic Versioning (SemVer)**
- **MAJOR.MINOR.PATCH** (예: 1.2.3)
- **MAJOR**: 호환성 깨지는 변경
- **MINOR**: 새 기능 추가 (하위 호환)
- **PATCH**: 버그 수정

#### **릴리스 주기**
- **Major**: 6개월 (새로운 기능, 아키텍처 변경)
- **Minor**: 1개월 (기능 추가, 개선)
- **Patch**: 1주일 (버그 수정, 보안 패치)

#### **호환성 정책**
- **SDK**: 최소 1년 하위 호환성 보장
- **API**: 최소 2년 하위 호환성 보장
- **노드**: 무한 하위 호환성 보장 (스키마 버전 관리)

### 15.2 배포 파이프라인

#### **CI/CD 파이프라인**
```yaml
# .github/workflows/release.yml
stages:
  - test:
      - unit_tests
      - integration_tests
      - performance_tests
      - security_scan

  - build:
      - package_sdk
      - build_documentation
      - create_artifacts

  - deploy:
      - staging_deployment
      - user_acceptance_test
      - production_deployment
      - post_deployment_tests
```

#### **배포 환경**
- **Development**: 매 커밋마다 자동 배포
- **Staging**: PR 머지 시 자동 배포
- **Production**: 수동 승인 후 배포

### 15.3 배포 채널

#### **SDK 배포**
1. **PyPI**: `pip install ai-canvas-sdk`
2. **GitHub Releases**: 바이너리 다운로드
3. **Docker**: `docker pull ai-canvas/sdk`
4. **Conda**: `conda install ai-canvas-sdk`

#### **문서 배포**
1. **공식 사이트**: https://docs.ai-canvas.io/sdk
2. **GitHub Pages**: 백업 및 버전별 문서
3. **PDF**: 오프라인 문서 다운로드

#### **예제 및 템플릿**
1. **GitHub Repository**: 예제 코드 저장소
2. **Starter Kits**: 즉시 사용 가능한 프로젝트 템플릿
3. **Jupyter Notebooks**: 인터랙티브 튜토리얼

### 15.4 롤백 전략

#### **자동 롤백 조건**
- 설치 성공률 < 90%
- 실행 성공률 < 95%
- 심각한 보안 취약점 발견
- 성능 저하 > 50%

#### **수동 롤백 프로세스**
1. 상황 평가 및 결정
2. 이전 버전으로 즉시 롤백
3. 근본 원인 분석
4. 핫픽스 개발 및 배포
5. 포스트모템 및 개선 계획

## 16. 문서 참조 및 리소스

### 16.1 기존 문서 링크
- [SDK 문서 홈](docs/ai-canvas-sdk/README.md)
- [설치 가이드](docs/ai-canvas-sdk/getting-started/installation.md)
- [빠른 시작](docs/ai-canvas-sdk/getting-started/quick-start.md)
- [시스템 아키텍처](docs/ai-canvas-sdk/concepts/architecture.md)
- [기본 노드 개발](docs/ai-canvas-sdk/guides/basic-node-development.md)
- [API 레퍼런스](docs/ai-canvas-sdk/api-reference/custom-node-class.md)
- [예제 노드](docs/ai-canvas-sdk/examples/data-processing-node.py)
- [FAQ 및 문제 해결](docs/ai-canvas-sdk/troubleshooting/faq.md)

### 16.2 외부 참조
- [gRPC Python Tutorial](https://grpc.io/docs/languages/python/)
- [Apache Arrow Python API](https://arrow.apache.org/docs/python/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery User Guide](https://docs.celeryproject.org/en/stable/)

### 16.3 표준 및 규격
- [Semantic Versioning](https://semver.org/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [JSON Schema](https://json-schema.org/)
- [gRPC Status Codes](https://grpc.github.io/grpc/core/md_doc_statuscodes.html)

### 16.4 내부 리소스
- AI Canvas 플랫폼 아키텍처 문서
- 백엔드 API 명세서
- 보안 정책 및 가이드라인
- 개발 환경 셋업 가이드

---

## 📞 연락처 및 지원

### 개발팀
- **Product Owner**: product@ai-canvas.io
- **Tech Lead**: tech-lead@ai-canvas.io
- **Backend Team**: backend@ai-canvas.io

### 지원 채널
- **기술 지원**: tech-support@ai-canvas.io
- **문서 피드백**: docs@ai-canvas.io
- **GitHub Issues**: [AI Canvas SDK Repository](https://github.com/AlgorithmLABS/ai-canvas-sdk/issues)

---

**문서 상태**: ✅ **승인됨**
**최종 업데이트**: 2025-09-17
**다음 검토**: 2025-10-01
**버전**: 1.0 (Unified)
**승인자**: CTO, VP of Engineering, Head of Security
