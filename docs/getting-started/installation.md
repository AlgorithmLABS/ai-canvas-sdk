# 설치 가이드

AI Canvas Custom Node SDK를 설치하고 로컬 CLI로 노드를 검증하는 환경을 만듭니다.

## 요구사항

- **Python 3.10 이상** (`requires-python = ">=3.10"`)
- pip 21 이상
- macOS 또는 Linux

런타임 의존성(설치 시 함께 들어옵니다): `pandas`, `numpy`, `pyarrow`, `grpcio`, `protobuf`.

> `grpcio-tools` / `pytest` 는 `[project.optional-dependencies] dev` 에만 있습니다. 노드를 만들고 CLI로 테스트하는 데는 기본 설치면 충분합니다. `scikit-learn` 은 SDK 의존성이 아닙니다.

## 설치

가상 환경을 권장합니다.

### venv

```bash
python3 -m venv ai-canvas-dev
source ai-canvas-dev/bin/activate

pip install "git+https://github.com/AlgorithmLABS/ai-canvas-sdk"
```

개발 브랜치(`dev`)를 쓰려면:

```bash
pip install "git+https://github.com/AlgorithmLABS/ai-canvas-sdk@dev"
```

### conda

```bash
conda create -n ai-canvas-dev python=3.12
conda activate ai-canvas-dev
pip install "git+https://github.com/AlgorithmLABS/ai-canvas-sdk"
```

로컬 체크아웃을 editable 로 설치하려면:

```bash
pip install -e .
```

## 설치 확인

```bash
ai-canvas-sdk --version
```

성공 시 **버전 문자열만** 출력됩니다. 예:

```
0.3.0
```

개발 설치라면 `0.3.0.dev7+g<sha>` 같은 setuptools-scm 형식일 수 있습니다.

`ai-canvas-sdk --help` 로 서브커맨드를 확인하세요. 현재 구현된 명령은 다음 두 가지입니다.

| 명령 | 용도 |
|------|------|
| `ai-canvas-sdk test <node.py>` | 로컬에서 스키마 검증 + `run()` 실행 |
| `ai-canvas-sdk register` | Git CI에서 백엔드에 노드 등록 (Flow A) |

`--version` 은 gRPC 연결이나 직렬화 점검을 하지 않습니다.

## 다음 단계

1. [빠른 시작](./quick-start.md) — 노드 하나 만들고 CLI로 실행
2. [로컬 CLI 테스트](../guides/local-cli-testing.md) — `-i` / `-p` / `-s` / `-o` 레퍼런스
3. [첫 번째 노드 만들기](./first-node.md) — 파라미터·검증이 있는 실무형 예제
