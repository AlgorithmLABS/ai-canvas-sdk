# AI Canvas Custom Node SDK – 제품 요구사항 문서 (PRD)

문서 버전: 0.1 (Draft)
작성일: 2025-09-17
문서 소유자: 백엔드

## 1. 배경과 목표
- 목표: 사용자가 README에 제시된 흐름대로 Custom Node를 직접 개발·실행·배포할 수 있는 Python 기반 SDK를 제공한다.
- Why now: ML/데이터 파이프라인 확장 요구 증가, 외부 파트너의 기능 제공 가속 필요.
- 성공 정의: 10분 내 첫 노드 생성/실행, 대용량 데이터 처리(>100K rows) 안정성, 보안 요구(mTLS) 충족.

## 2. 사용자와 사용 시나리오
- 페르소나
  - 데이터 엔지니어/사이언티스트: 사내/외부 데이터 처리 로직을 노드로 제공
  - 파트너 개발자: 자체 모델/서비스를 캔버스에서 호출 가능한 노드로 포장
- 주요 시나리오
  1) SDK 설치 → 템플릿 복사 → `run`으로 로컬 검증 → `package/register/publish`로 배포 → 캔버스에서 사용
  2) 대용량 데이터(Parquet/Arrow) 입출력, 진행률/로그 스트리밍, 실패 시 원인 파악(트러블슈팅)

## 3. 범위
- In Scope
  - SDK 코어: `CustomNode`, `NodeSchema`, `NodeContext` 인터페이스와 런타임 실행 루프
  - gRPC 통신(단건/스트리밍) 및 mTLS, 실행 취소/타임아웃/멱등성 훅
  - 데이터 직렬화 계층: JSON 메타데이터 + Parquet/Arrow(공유 볼륨 경유 경로 교환)
  - CLI: `run`, `test`, `package`, `register`, `profile`, `publish`, `--version`, `test-connection`
  - 문서/예제: Getting Started, 기본/고급 가이드, API 레퍼런스, 예제 노드, FAQ
- Out of Scope
  - 백엔드 DAG/워크플로우 편집기 기능 개선 자체(호출자)
  - Python 외 다국어 SDK(후속)
  - 원격 오브젝트 스토리지 직접 통합(공유 볼륨 우선)

## 4. 요구사항
### 4.1 기능 요구사항 (FR)
- FR1: 개발자는 `CustomNode.run(inputs: dict, parameters: dict, ctx: NodeContext) -> dict`만 구현하면 노드 동작
- FR2: `NodeSchema`로 입력/출력/파라미터/메타를 선언하고 런타임에서 스키마 검증 수행
- FR3: gRPC 서비스와 양방향(서버 스트리밍) 실행 이벤트 전달(로그/진행률/부분결과)
- FR4: 데이터 교환은 메타 JSON + 대용량은 Parquet/Arrow 파일 경로(`file:///data/...`)로 처리
- FR5: 실행 제어(취소/타임아웃/멱등성) 지원, 실패/재시도 정책 노출
- FR6: CLI 제공: 로컬 실행/테스트/패키징/등록/프로파일/배포 수행
- FR7: 예제 노드(HelloWorld/데이터 필터/스트리밍/ML)와 템플릿 제공
- FR8: 문서(설치/빠른시작/개념/가이드/API/문제해결) 완비

### 4.2 비기능 요구사항 (NFR)
- NFR1 성능: 10만 행 DataFrame 기준 Parquet 입출력 end-to-end < 1.0s(환경 의존, I/O 제외), 직렬화 오버헤드 < 400ms 지향
- NFR2 안정성: 취소/타임아웃 시 리소스/임시파일 정리, 부분결과 미노출(원자적 rename)
- NFR3 보안: 전 gRPC 호출 mTLS, 공유 볼륨 최소 권한(예: 770), 이미지 서명/스캔 정책 준수
- NFR4 호환성: Python 3.10+ 지원, Arrow/Parquet 의존성 감지와 우회 설치 가이드 제공
- NFR5 관측성: 진행률, 구조화 로그, 실행 메트릭(시간/메모리/네트워크) 수집/표준화

## 5. 아키텍처 및 설계 방향
- 호출 경로: Frontend → Backend(FastAPI) → Queue(Celery/Redis) → DAG Worker → gRPC(Custom Node Server) → SDK 노드
- gRPC 서비스:
  - ExecuteNode(NodeRequest) → NodeResponse
  - ExecuteNodeStream(NodeRequest) → stream NodeProgress
  - RegisterNode(NodeDefinition) → RegistrationResult
  - HealthCheck(HealthRequest) → HealthResponse
- 데이터 직렬화 계층
  - 메타: JSON, 데이터: Arrow/Parquet(공유 볼륨). SDK/플랫폼은 파일 경로만 교환
  - 네임스페이스: `/data/{canvas_id}/{node_id}/{run_id}/...`, 임시파일에 쓰고 커밋 시 rename
- 실행 이벤트/상태 전이
  - 상태: PENDING → RUNNING → SUCCESS/FAILED/TIMEOUT/CANCELLED (+RETRY)
  - NodeContext: `log_*`, `progress(float)`, `emit_partial(name, value)` API 제공
- 실행 제어
  - 취소: gRPC Cancel 신호 수신 후 안전 중단
  - 타임아웃: 런타임 상한 초과 시 종료, 임시 산출물 정리
  - 멱등성: `idempotency_key`로 중복 실행 방지, 캐시/산출물 재사용 옵션
- 보안
  - 모든 gRPC 호출 mTLS, 인증서 로테이션/배포 가이드 포함
  - 공유 볼륨 접근 최소 권한, rootless 컨테이너 권장

## 6. SDK 인터페이스(개발자 경험)
- 핵심 타입
  - `CustomNode`: 베이스 클래스. `run()` 구현, 수명주기 훅(optional)
  - `NodeSchema`: name, display_name, description, category, version, inputs, outputs, parameters
  - `NodeContext`: 로그·진행률·메트릭·취소플래그·산출물 경로 헬퍼
  - `PortType`: TEXT, JSON, DATAFRAME/DATASET, DISPLAY 등
- 템플릿/예외 처리
  - 스키마 기반 검증 실패 시 명확한 메시지와 해결 가이드 제공
  - 리소스 한도 초과/입출력 오류/데이터 유효성 실패에 대한 표준 예외 체계

## 7. CLI 명세(요약)
- `ai-canvas-sdk --version` / `test-connection`
- `run <node.py> [--input JSON|--input-file path] [--params JSON] [--test]`
- `test <node.py> [--sample-data]`
- `package --nodes <files...> --output <zip> --version <semver>`
- `register --package <zip> --server <url> --api-key <key>`
- `publish <manifest.json>`
- `profile <node.py> --input JSON --iterations N`

## 8. 문서/예제 범위
- Getting Started: 설치, 빠른 시작, 첫 노드 만들기
- Concepts: 아키텍처, 데이터 타입/직렬화, 노드 생명주기
- Guides: 기본 노드 개발(템플릿/모범사례), 고급 기능(스트리밍/성능/취소/멱등성)
- API Reference: `CustomNode`, `NodeSchema`, 직렬화 설정
- Examples: HelloWorld, DataFilter, Streaming, ML Training, API 연동
- Troubleshooting: FAQ, 설치/네트워크/권한/의존성 문제 해결

## 9. 테스트 전략과 수용 기준
- 단위 테스트
  - 스키마 검증, 타입 직렬화/역직렬화, NodeContext 로깅/진행률, 취소/타임아웃 훅
- 통합 테스트
  - gRPC Execute/Stream 경로, 공유 볼륨 파일 I/O 원자성, 패키징/등록/퍼블리시 흐름
- 성능/대용량 테스트
  - 10만 행 DataFrame, Arrow/Parquet throughput 측정, 진행률 이벤트 지연 측정
- 수용 기준(Acceptance)
  - A1: HelloWorld 템플릿으로 `run --test` 성공 및 진행률/로그 출력
  - A2: DataFilter 예제로 Parquet 입출력 성공, 통계 산출
  - A3: `cancel` 시 안전 중단 및 임시파일 정리 확인
  - A4: `profile` 결과에 평균 실행시간/메모리/직렬화/네트워크 지표 표준 포맷 노출
  - A5: `package/register/publish` 후 캔버스에서 노드 사용 가능

## 10. 마일스톤/일정(스텝 기반)
- M1 Kickoff & Architecture(주 1)
  - 산출물: 상세 설계서, Proto 스키마 초안, 보안/취소/멱등성 정책
- M2 Environment & Toolchain(주 1)
  - 산출물: 가상환경 스크립트, 설치/헬스체크, 방화벽 가이드
- M3 SDK Core Scaffold(주 2)
  - 산출물: `CustomNode/NodeSchema/NodeContext`, 템플릿/HelloWorld, 타입 검증
- M4 Runtime & Data Handling(주 2)
  - 산출물: gRPC 실행/스트리밍, Arrow/Parquet, 공유 볼륨 정책, 취소/타임아웃/멱등성
- M5 CLI & DX(주 1)
  - 산출물: run/test/package/register/profile/publish, 로깅 규약
- M6 QA, Docs & Release(주 1)
  - 산출물: 테스트/성능 보고서, 문서/예제, 보안 점검, 릴리스 노트

## 11. 성공 지표(KPI)
- TTFHello: 설치 후 첫 노드 실행까지 < 10분(문서만 보고)
- 실패율: 로컬 실행/패키징/등록 과정 합산 실패율 < 2%
- 성능: 10만 행 기준 직렬화+전송+역직렬화 95p < 1.5s(동일 호스트)
- 안정성: 강제 취소/타임아웃 시 잔여 임시파일 0, 재시작 성공률 > 99%

## 12. 리스크와 대응
- PyArrow/GRPC 빌드 실패: 사전 의존성 체크·대안 설치 가이드 제공, `--no-binary` 재시도 옵션 안내
- 공유 볼륨 권한 문제: 표준 UID/GID/마운트 가이드, 권장 권한(770)와 루트리스 권장
- 대용량 메모리 압박: 청크 처리·열 선택·사전 필터 모범사례와 샘플 코드 제공
- 네트워크 지연/불안정: 스트리밍 이벤트 백오프/재시도, 타임아웃 튜닝 옵션 노출

## 13. 의존성/전제조건
- Backend: external_grpc 실행 경로 지원, 레지스트리 조회/캐시 무효화 이벤트
- Infra: gRPC 엔드포인트(mTLS)·공유 볼륨·로그 수집 경로 확보
- 보안: 인증서 발급/로테이션 절차, 이미지 서명/스캔 파이프라인

## 14. 오픈 이슈
- PortType 상세 분류(데이터셋/데이터프레임/디스플레이) 최종 정의
- 멱등성 키 범위와 캐시 정책(입력 파라미터 해시 포함 여부)
- SDK 배포 채널(PyPI/내부 레지스트리)와 버전 호환 정책

## 15. 릴리스/배포
- 버전: SemVer, `MAJOR.MINOR.PATCH`
- 배포: 패키지(내부 레지스트리 or PyPI), `publish manifest.json`로 노드 레지스트리 등록
- 문서: Getting Started/Guides/API/Examples/FAQ 동시 공개, 변경 로그 제공

## 16. 문서 참조
- docs/ai-canvas-sdk/README.md
- docs/ai-canvas-sdk/getting-started/installation.md
- docs/ai-canvas-sdk/getting-started/quick-start.md
- docs/ai-canvas-sdk/concepts/architecture.md
- docs/ai-canvas-sdk/guides/basic-node-development.md
- docs/ai-canvas-sdk/troubleshooting/faq.md

