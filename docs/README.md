# AI Canvas Custom Node SDK Documentation

AI Canvas Custom Node SDK로 자체 데이터 처리 노드를 만들고, 로컬 CLI로 검증하는 방법을 안내합니다.

## 문서 지도

| 문서 | 내용 |
|------|------|
| [설치](./getting-started/installation.md) | pip/venv/conda, `--version` 출력 |
| [빠른 시작](./getting-started/quick-start.md) | 노드 하나 + `ai-canvas-sdk test` |
| [첫 번째 노드](./getting-started/first-node.md) | 파라미터·검증이 있는 필터 노드 |
| [로컬 CLI 테스트](./guides/local-cli-testing.md) | `-i` / `-p` / `-s` / `-o` 레퍼런스 |
| [기본 노드 개발](./guides/basic-node-development.md) | 스키마·`run()` 패턴 |
| [Secret 사용](./guides/using-secrets.md) | `required_secrets` / `ctx.get_secret` |
| [CustomNode API](./api-reference/custom-node-class.md) | 공개 클래스·필드 |
| [데이터 타입](./concepts/data-types.md) | `PortTypeEnum` 과 직렬화 임계값 |
| [CI 등록](./ci/README.md) | `ai-canvas-sdk register` (GitHub/GitLab) |

예제 코드: [`docs/examples/hello_node.py`](./examples/hello_node.py), [`docs/examples/public-data-node.py`](./examples/public-data-node.py) (secret 주입).

## 개요

Custom Node SDK는 `get_schema()` 와 `run()` 만 구현하면 됩니다. gRPC·직렬화·캔버스 UI 등록은 플랫폼이 담당합니다.

```
┌─────────┐    ┌─────────┐    ┌─────┐    ┌──────────────┐    ┌─────────────┐
│ Client  │───▶│ Backend │───▶│ DAG │───▶│ Custom Node  │───▶│ Your Node   │
└─────────┘    └─────────┘    └─────┘    │   Server     │    │   (SDK)     │
                                         │   (gRPC)     │    │             │
                                         └──────────────┘    └─────────────┘
```

로컬에서는 이 경로를 타지 않습니다. `ai-canvas-sdk test` 가 노드 파일을 로드해 스키마를 검사하고 `run()` 을 직접 호출합니다.

## 빠른 시작

### 1. 설치

```bash
pip install "git+https://github.com/AlgorithmLABS/ai-canvas-sdk"
ai-canvas-sdk --version
```

버전 문자열만 출력됩니다 (헬스체크 배너는 없습니다).

### 2. 첫 번째 노드

```python
from ai_canvas_sdk import (
    CustomNode, NodeSchema, NodeData, Port,
    PortEnum, PortTypeEnum, PositionEnum, NodeContext,
)

class HelloWorldNode(CustomNode):
    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="HelloWorld",
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="input_data",
                    ),
                ],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="output_data",
                    ),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs.get("input_data")
        ctx.log_info("processing hello")
        ctx.progress(0.5)
        return {"output_data": df}
```

### 3. 로컬 테스트

```bash
ai-canvas-sdk test hello_world.py
ai-canvas-sdk test hello_world.py --validate-only
ai-canvas-sdk test hello_world.py -i input_data.json -p '{"message": "Hello"}' -o result.json -v
```

#### `test` 옵션

| 옵션 | 단축 | 설명 |
|------|------|------|
| `node_file` | | (필수) 테스트할 노드 파일 경로 |
| `--class` | | 파일에 노드 클래스가 여러 개일 때 지정 |
| `--validate-only` | | 스키마 검증만 수행, `run()` 하지 않음 |
| `--input` | `-i` | 입력 JSON 또는 CSV |
| `--params` | `-p` | 파라미터 JSON 문자열 |
| `--secret` | `-s` | secret `KEY=VALUE` (여러 번 지정 가능). Secret Store 에 접속하지 않음 |
| `--output` | `-o` | 결과 JSON 또는 CSV |
| `--verbose` | `-v` | 스키마 경고 포함 |

#### 입력 데이터 형식

- **JSON (포트별):** `{"port_label": [{"col": "val"}, ...]}`
- **JSON (배열):** `[{"col": "val"}, ...]` — 첫 번째 입력 포트에 할당
- **CSV:** 첫 번째 입력 포트에 할당
- **`-i` 생략:** 각 입력 포트에 빈 DataFrame

로그와 진행률은 stderr 로 출력됩니다.

## 배포/등록

| 명령 | 역할 |
|------|------|
| `ai-canvas-sdk test` | 로컬 스키마 검증 + `run()` |
| `ai-canvas-sdk register` | CI에서 백엔드에 노드 upsert (Flow A) |
| `ai-canvas-sdk --version` | 패키지 버전 |

`register` 는 로컬 개발용 배포 도구가 아닙니다. 레포 레이아웃(`<NodeSchema.name>/main.py`)과 OAuth client 가 필요합니다. → [CI 등록 가이드](./ci/README.md)

## 실행 제어 (플랫폼 런타임)

로컬 `test` 에는 해당하지 않습니다. 캔버스에서 실행될 때:

- **취소**: `ctx.is_cancelled()` 로 확인 (로컬 테스트 컨텍스트는 항상 `False`)
- **타임아웃**: 런타임이 작업 컨테이너를 종료
- **대용량 데이터**: gRPC 로는 경로만 교환하고 공유 볼륨(`file:///data/...`)을 사용

## 보안

- 플랫폼 gRPC 는 mTLS 를 사용합니다.
- API 키는 코드에 넣지 말고 `required_secrets` + `ctx.get_secret` 을 쓰세요. [Secret 가이드](./guides/using-secrets.md)

---

**다음 단계**: [설치 가이드](./getting-started/installation.md)
