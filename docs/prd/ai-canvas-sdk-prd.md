# AI Canvas Custom Node SDK - Product Requirements Document (PRD)

## 1. 제품 개요

### 1.1 제품명
AI Canvas Custom Node SDK

### 1.2 제품 설명
AI Canvas Custom Node SDK는 개발자가 AI Canvas 플랫폼에서 사용할 수 있는 커스텀 노드를 쉽게 개발, 테스트, 배포할 수 있도록 지원하는 소프트웨어 개발 키트입니다.

### 1.3 목적
- 외부 개발자가 AI Canvas 생태계를 확장할 수 있도록 지원
- 커스텀 비즈니스 로직을 노드 형태로 구현 가능
- 재사용 가능한 컴포넌트 생성 및 공유

### 1.4 대상 사용자
- Python 개발자
- 데이터 사이언티스트
- ML 엔지니어
- AI Canvas 플랫폼 사용 기업의 개발팀

## 2. 핵심 기능 요구사항

### 2.1 노드 정의 시스템

#### 2.1.1 데코레이터 기반 노드 정의
```python
@custom_node(
    name="DataFilter",
    category="data_processing",
    version="1.0.0",
    description="Filter data based on conditions"
)
class DataFilterNode(CustomNodeBase):
    pass
```

**요구사항:**
- 간단한 데코레이터로 노드 메타데이터 정의
- 버전 관리 지원
- 카테고리 분류 시스템
- 다국어 설명 지원

#### 2.1.2 포트 정의
```python
input_ports = [
    InputPort(name="data", type=PortType.DATASET, required=True),
    InputPort(name="threshold", type=PortType.NUMBER, default=0.5)
]
output_ports = [
    OutputPort(name="filtered_data", type=PortType.DATASET),
    OutputPort(name="stats", type=PortType.JSON)
]
```

**요구사항:**
- 다양한 데이터 타입 지원 (Dataset, Model, Number, String, Boolean, JSON, File)
- 필수/선택 포트 구분
- 기본값 설정 가능
- 포트 검증 로직

#### 2.1.3 파라미터 시스템
```python
parameters = [
    IntParameter("batch_size", min=1, max=1000, default=32),
    FloatParameter("learning_rate", min=0.0001, max=1.0, default=0.001),
    SelectParameter("algorithm", choices=["kmeans", "dbscan"], default="kmeans"),
    StringParameter("api_key", secret=True, required=True),
    BoolParameter("enable_cache", default=True)
]
```

**요구사항:**
- 다양한 파라미터 타입
- 검증 규칙 (min, max, regex, choices)
- UI 위젯 타입 자동 매핑
- 비밀 정보 처리 (API 키 등)

### 2.2 실행 엔진

#### 2.2.1 실행 메서드
```python
def execute(self, context: ExecutionContext, **inputs) -> dict:
    # 노드 실행 로직
    df = inputs['data']
    threshold = inputs['threshold']
    
    # 진행 상황 리포팅
    context.report_progress(50, "Processing data...")
    
    # 로깅
    context.log.info(f"Processing {len(df)} rows")
    
    # 결과 반환
    return {
        'filtered_data': filtered_df,
        'stats': {'rows_filtered': count}
    }
```

**요구사항:**
- 비동기 실행 지원
- 진행 상황 리포팅
- 구조화된 로깅
- 메모리 효율적 데이터 처리
- 에러 처리 및 복구

#### 2.2.2 실행 컨텍스트
```python
class ExecutionContext:
    def report_progress(self, percentage: int, message: str)
    def log.info/debug/warning/error(message: str)
    def get_temp_directory() -> Path
    def get_resource(name: str) -> Any
    def set_metadata(key: str, value: Any)
```

**요구사항:**
- 실행 환경 정보 제공
- 리소스 관리
- 임시 파일 처리
- 메타데이터 저장

### 2.3 노드 레지스트리

#### 2.3.1 노드 등록
```python
registry = NodeRegistry()
registry.register(DataFilterNode)
registry.register_from_module("my_custom_nodes")
registry.register_from_directory("./nodes")
```

**요구사항:**
- 프로그래매틱 등록
- 모듈/디렉토리 기반 자동 스캔
- 중복 등록 방지
- 버전 충돌 관리

#### 2.3.2 노드 검색
```python
nodes = registry.search(category="data_processing")
nodes = registry.search(tags=["ml", "preprocessing"])
node = registry.get("DataFilter", version="1.0.0")
```

**요구사항:**
- 카테고리별 검색
- 태그 기반 검색
- 버전별 조회
- 메타데이터 필터링

### 2.4 테스팅 프레임워크

#### 2.4.1 단위 테스트
```python
def test_data_filter_node():
    node = DataFilterNode()
    context = MockExecutionContext()
    
    result = node.execute(
        context,
        data=test_dataframe,
        threshold=0.5
    )
    
    assert len(result['filtered_data']) == expected_count
```

**요구사항:**
- Mock 실행 컨텍스트
- 테스트 픽스처
- 입출력 검증 도구
- 성능 테스트 지원

#### 2.4.2 통합 테스트
```python
@integration_test
async def test_node_in_workflow():
    workflow = Workflow()
    workflow.add_node(DataFilterNode())
    workflow.add_node(DataAggregationNode())
    workflow.connect("filter.output", "aggregation.input")
    
    result = await workflow.execute(test_data)
    assert result.success
```

**요구사항:**
- 워크플로우 내 테스트
- 노드 간 연결 테스트
- 비동기 실행 테스트
- 에러 시나리오 테스트

### 2.5 CLI 도구

#### 2.5.1 프로젝트 초기화
```bash
$ aicanvas-sdk init my-custom-node
Creating new custom node project: my-custom-node
✓ Project structure created
✓ Dependencies installed
✓ Example node generated
```

**요구사항:**
- 프로젝트 템플릿 생성
- 의존성 자동 설정
- 예제 코드 포함

#### 2.5.2 노드 검증
```bash
$ aicanvas-sdk validate my_node.py
Validating node: my_node.py
✓ Syntax check passed
✓ Port definitions valid
✓ Parameter definitions valid
✓ Execute method implemented
⚠ Warning: Missing unit tests
```

**요구사항:**
- 문법 검사
- 스키마 검증
- 베스트 프랙티스 체크
- 경고 및 제안사항

#### 2.5.3 로컬 테스트
```bash
$ aicanvas-sdk test my_node.py --input data.csv
Running node locally...
✓ Node executed successfully
Output saved to: output/result.json
Execution time: 2.3s
Memory usage: 124MB
```

**요구사항:**
- 로컬 실행 환경
- 테스트 데이터 입력
- 실행 메트릭 수집
- 디버그 모드

#### 2.5.4 배포
```bash
$ aicanvas-sdk deploy my_node.py --environment production
Deploying node to production...
✓ Node validated
✓ Dependencies resolved
✓ Node registered in registry
✓ Available in AI Canvas platform
Node ID: custom-node-abc123
```

**요구사항:**
- 환경별 배포
- 의존성 패키징
- 버전 태깅
- 롤백 지원

## 3. 기술 요구사항

### 3.1 언어 및 프레임워크
- **Primary SDK**: Python 3.8+
- **Secondary SDK**: TypeScript/JavaScript (Phase 2)
- **Dependencies**: 
  - pydantic >= 2.0
  - pandas
  - numpy
  - asyncio

### 3.2 호환성
- AI Canvas 플랫폼 버전 2.0+
- FastAPI 백엔드 통합
- Celery 워커 시스템 호환
- MongoDB 데이터 저장소

### 3.3 성능 요구사항
- 노드 초기화: < 100ms
- 메모리 사용량: < 512MB per node instance
- 동시 실행: 최대 100개 노드
- 데이터 처리: 1GB 데이터셋 처리 가능

### 3.4 보안 요구사항
- 샌드박스 실행 환경
- 코드 서명 및 검증
- API 키 암호화
- 리소스 접근 제한
- 악성 코드 스캔

## 4. API 명세

### 4.1 REST API

#### 4.1.1 노드 등록
```http
POST /api/v1/custom-nodes/register
Content-Type: application/json

{
  "name": "DataFilter",
  "version": "1.0.0",
  "source_code": "base64_encoded_code",
  "dependencies": ["pandas>=1.3.0"],
  "metadata": {
    "author": "developer@example.com",
    "license": "MIT"
  }
}
```

#### 4.1.2 노드 목록 조회
```http
GET /api/v1/custom-nodes?category=data_processing&page=1&limit=20
```

#### 4.1.3 노드 실행
```http
POST /api/v1/custom-nodes/{node_id}/execute
Content-Type: application/json

{
  "inputs": {
    "data": "dataset_id_123",
    "threshold": 0.5
  },
  "parameters": {
    "batch_size": 32
  }
}
```

#### 4.1.4 노드 삭제
```http
DELETE /api/v1/custom-nodes/{node_id}
```

### 4.2 Python SDK API

#### 4.2.1 기본 클래스
```python
class CustomNodeBase:
    def __init__(self)
    def define_inputs(self) -> List[InputPort]
    def define_outputs(self) -> List[OutputPort]
    def define_parameters(self) -> List[Parameter]
    def execute(self, context: ExecutionContext, **inputs) -> dict
    def validate(self) -> ValidationResult
```

#### 4.2.2 포트 클래스
```python
class Port:
    def __init__(self, name: str, type: PortType, **kwargs)
    def validate_data(self, data: Any) -> bool
    def transform_data(self, data: Any) -> Any

class InputPort(Port):
    def __init__(self, name: str, type: PortType, required: bool = True, default: Any = None)

class OutputPort(Port):
    def __init__(self, name: str, type: PortType, optional: bool = False)
```

#### 4.2.3 파라미터 클래스
```python
class Parameter:
    def __init__(self, name: str, **kwargs)
    def validate(self, value: Any) -> bool
    def to_ui_schema(self) -> dict

class IntParameter(Parameter):
    def __init__(self, name: str, min: int = None, max: int = None, default: int = None)

class FloatParameter(Parameter):
    def __init__(self, name: str, min: float = None, max: float = None, default: float = None)

class SelectParameter(Parameter):
    def __init__(self, name: str, choices: List[str], default: str = None)
```

## 5. 사용자 경험 (UX)

### 5.1 개발자 워크플로우
1. **설치**: `pip install aicanvas-sdk`
2. **프로젝트 생성**: `aicanvas-sdk init`
3. **노드 개발**: 코드 작성
4. **로컬 테스트**: `aicanvas-sdk test`
5. **검증**: `aicanvas-sdk validate`
6. **배포**: `aicanvas-sdk deploy`
7. **모니터링**: AI Canvas 플랫폼에서 실행 모니터링

### 5.2 문서화
- **Getting Started Guide**: 15분 내 첫 노드 생성
- **API Reference**: 전체 API 문서
- **Tutorial**: 단계별 튜토리얼
- **Best Practices**: 권장 사항 및 패턴
- **Examples Gallery**: 예제 노드 모음

### 5.3 개발 도구 통합
- **VS Code Extension**: 자동완성, 스니펫, 디버깅
- **IntelliJ Plugin**: IDE 통합
- **GitHub Actions**: CI/CD 템플릿

## 6. 성공 지표 (KPI)

### 6.1 채택 지표
- 월간 활성 개발자 수 (MAD): 목표 1,000명
- 생성된 커스텀 노드 수: 목표 5,000개
- 노드 실행 횟수: 월 100만 회

### 6.2 품질 지표
- SDK 설치 성공률: > 95%
- 첫 노드 생성까지 시간: < 30분
- 노드 실행 성공률: > 99%
- 평균 응답 시간: < 500ms

### 6.3 개발자 만족도
- NPS (Net Promoter Score): > 50
- 문서 만족도: > 4.0/5.0
- 지원 응답 시간: < 24시간

## 7. 로드맵

### Phase 1: MVP (3개월)
- [x] 기본 노드 정의 시스템
- [x] Python SDK 핵심 기능
- [x] CLI 도구 기본 기능
- [x] 기본 문서화

### Phase 2: 확장 (2개월)
- [ ] TypeScript/JavaScript SDK
- [ ] 고급 테스팅 프레임워크
- [ ] VS Code Extension
- [ ] 노드 마켓플레이스 통합

### Phase 3: 엔터프라이즈 (2개월)
- [ ] 프라이빗 레지스트리
- [ ] 팀 협업 기능
- [ ] 고급 보안 기능
- [ ] 성능 프로파일링 도구

### Phase 4: 생태계 (진행중)
- [ ] 커뮤니티 노드 허브
- [ ] 노드 인증 프로그램
- [ ] 파트너 통합
- [ ] 교육 프로그램

## 8. 리스크 및 완화 방안

### 8.1 기술적 리스크
- **리스크**: 악성 코드 실행
  - **완화**: 샌드박스 환경, 코드 검증, 리소스 제한

- **리스크**: 성능 저하
  - **완화**: 비동기 실행, 캐싱, 리소스 풀링

- **리스크**: 버전 호환성
  - **완화**: 시맨틱 버저닝, 하위 호환성 보장

### 8.2 비즈니스 리스크
- **리스크**: 낮은 개발자 채택률
  - **완화**: 우수한 문서화, 튜토리얼, 커뮤니티 구축

- **리스크**: 품질 관리
  - **완화**: 자동 테스트, 코드 리뷰, 인증 프로그램

## 9. 종속성 및 제약사항

### 9.1 기술적 종속성
- AI Canvas 플랫폼 백엔드
- MongoDB 데이터베이스
- Redis 캐시
- Celery 워커 시스템

### 9.2 제약사항
- Python 3.8+ 필수
- 최대 파일 크기: 10MB
- 실행 시간 제한: 30분
- 메모리 제한: 2GB

## 10. 부록

### 10.1 용어집
- **Custom Node**: 사용자가 정의한 AI Canvas 노드
- **Port**: 노드 간 데이터 전달 인터페이스
- **Parameter**: 노드 실행 시 설정 가능한 옵션
- **Registry**: 커스텀 노드 저장소
- **Execution Context**: 노드 실행 환경 정보

### 10.2 참고 문서
- AI Canvas Platform Documentation
- FastAPI Documentation
- Celery Documentation
- Pydantic Documentation

### 10.3 연락처
- Product Owner: product@aicanvas.com
- Tech Lead: tech@aicanvas.com
- Support: support@aicanvas.com

---

*Last Updated: 2024*
*Version: 1.0.0*
*Status: Draft*