# 설치 가이드

AI Canvas Custom Node SDK를 설치하고 개발 환경을 설정하는 방법을 안내합니다.

## 시스템 요구사항

### Python 버전
- **Python 3.10 이상** (권장: Python 3.11+)
- pip 21.0 이상

### 운영체제
- Linux (Ubuntu 24.04+, CentOS 7+)
- macOS 12.7+

### 하드웨어
- **메모리**: 최소 4GB, 권장 8GB+
- **디스크**: 최소 1GB 여유 공간
- **네트워크**: gRPC 서버 접근 가능한 환경

## 설치 방법

### 1. 기본 설치

```bash
# 기본 SDK 설치 (가벼운 버전)
pip install "git+https://github.com/AlgorithmLABS/ai-canvas-sdk"
```

이 설치는 다음 런타임 의존성을 함께 설치합니다(`pyproject.toml` 기준):
- `grpcio`: gRPC 런타임
- `protobuf`: Protocol Buffers 메시지
- `pandas`: DataFrame 기반 데이터 처리
- `pyarrow`: Apache Arrow/Parquet 직렬화
- `numpy`: 수치 연산

> 개발용 도구(`grpcio-tools`, `mypy-protobuf`, `pytest` 등)는 optional-dependencies(예: `pip install "ai-canvas-sdk[dev]"`)로 분리되어 있어 기본 설치에는 포함되지 않습니다.

## 가상 환경 설정 (권장)

프로젝트별 독립적인 환경 구성:

### venv 사용
```bash
# 가상 환경 생성
python -m venv ai-canvas-dev
source ai-canvas-dev/bin/activate  # Linux/macOS

# SDK 설치
pip install "git+https://github.com/AlgorithmLABS/ai-canvas-sdk"

```

### conda 사용
```bash
# conda 환경 생성
conda create -n ai-canvas-dev python=3.10
conda activate ai-canvas-dev

# SDK 설치
pip install "git+https://github.com/AlgorithmLABS/ai-canvas-sdk"
```

## 설치 확인

설치가 완료되었는지 확인:

```bash
# SDK 버전 확인
ai-canvas-sdk --version

```

성공적으로 설치되었다면 설치된 버전 문자열이 한 줄로 출력됩니다:

```
0.3.0.dev7+gcad704b18
```

버전 문자열은 설치 시점에 따라 달라집니다(정식 릴리즈는 `vX.Y.Z` 태그 기준). CLI가 제공하는 명령은 다음과 같습니다:

```bash
ai-canvas-sdk --help
# commands:
#   test       커스텀 노드를 로컬에서 테스트합니다.
#   register   custom node 를 backend 에 등록 (CI push 경로)
```

## 다음 단계

설치가 완료되었다면:

1. **[빠른 시작 가이드](./quick-start.md)**로 첫 번째 노드 실행
2. **[첫 번째 노드 만들기](./first-node.md)**로 개발 시작
3. **[개념 문서](../concepts/architecture.md)**로 아키텍처 이해

