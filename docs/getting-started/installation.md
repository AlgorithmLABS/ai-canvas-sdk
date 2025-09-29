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
pip install ai-canvas-sdk
```

이 설치는 다음 추가 패키지를 포함합니다:
- `pyarrow`: Apache Arrow/Parquet 지원
- `grpcio-tools`: Protocol Buffers 컴파일러
- `scikit-learn`: ML 모델 지원

## 가상 환경 설정 (권장)

프로젝트별 독립적인 환경 구성:

### venv 사용
```bash
# 가상 환경 생성
python -m venv ai-canvas-dev
source ai-canvas-dev/bin/activate  # Linux/macOS

# SDK 설치
pip install ai-canvas-sdk
```

### conda 사용
```bash
# conda 환경 생성
conda create -n ai-canvas-dev python=3.10
conda activate ai-canvas-dev

# SDK 설치
pip install ai-canvas-sdk
```

## 설치 확인

설치가 완료되었는지 확인:

```bash
# SDK 버전 확인
ai-canvas-sdk --version

# 기본 기능 테스트
ai-canvas-sdk test-connection
```

성공적으로 설치되었다면 다음과 유사한 출력을 볼 수 있습니다:

```
AI Canvas Custom Node SDK v1.0.0
✓ Python version: 3.10.12
✓ gRPC connection: OK
✓ Serialization: OK (Parquet/Arrow available)
✓ Installation complete!
```

## 네트워크 설정

### 방화벽 설정
gRPC 통신을 위한 포트 개방:

```bash
# Linux (iptables)
sudo iptables -A INPUT -p tcp --dport 50051 -j ACCEPT

# 또는 ufw 사용
sudo ufw allow 50051
```

## 문제 해결

### 설치 오류

#### PyArrow 설치 실패
```bash
# 시스템 패키지 먼저 설치
# Ubuntu/Debian
sudo apt-get install libarrow-dev

# macOS
brew install apache-arrow

# 그 후 재설치
pip install --no-cache-dir pyarrow
```

#### gRPC 컴파일 오류
```bash
# 컴파일러 도구 설치
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install
```

### 네트워크 연결 문제

```bash
# gRPC 서버 연결 테스트
telnet your-server.com 50051

# 또는
nc -zv your-server.com 50051
```

### 권한 문제
```bash
# 가상 환경 사용 (권장)
python -m venv venv && source venv/bin/activate
```

## 다음 단계

설치가 완료되었다면:

1. **[빠른 시작 가이드](./quick-start.md)**로 첫 번째 노드 실행
2. **[첫 번째 노드 만들기](./first-node.md)**로 개발 시작
3. **[개념 문서](../concepts/architecture.md)**로 아키텍처 이해

