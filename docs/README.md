# AI Canvas Custom Node SDK Documentation

AI Canvas Custom Node SDK를 사용하여 자체 데이터 처리 노드를 개발하는 방법을 안내합니다.

## 개요

AI Canvas는 시각적 워크플로우 빌더를 통해 ML 파이프라인을 구성하고 실행할 수 있는 플랫폼입니다. Custom Node SDK를 사용하면 비즈니스 로직에만 집중하여 새로운 노드를 개발할 수 있습니다.

### 주요 특징

- **gRPC 통신 + mTLS 보안**: Protocol Buffers 기반 바이너리 프로토콜, 양단 인증 지원
- **표준화된 직렬화**: 메타데이터는 JSON, 대용량 데이터셋/파일은 Parquet/Arrow 기반(공유 볼륨 경유)
- **실행 이벤트 스트리밍**: 로그/진행률/부분결과를 서버 스트리밍으로 전달
- **타입 안정성**: 런타임 스키마 검증(Pydantic/Protobuf) + 선택적 mypy 정적 점검
- **간단한 인터페이스**: run() 메서드만 구현하면 완료, NodeContext 제공

### 아키텍처 개요

```
┌─────────┐    ┌─────────┐    ┌─────┐    ┌──────────────┐    ┌─────────────┐
│ Client  │───▶│ Backend │───▶│ DAG │───▶│ Custom Node  │───▶│ Your Node   │
└─────────┘    └─────────┘    └─────┘    │   Server     │    │   (SDK)     │
                                         │   (gRPC)     │    │             │
                                         └──────────────┘    └─────────────┘
```

## 문서 구조

### [Getting Started](./getting-started/)
- [설치 가이드](./getting-started/installation.md)
- [빠른 시작](./getting-started/quick-start.md)
- [첫 번째 노드 만들기](./getting-started/first-node.md)

### [핵심 개념](./concepts/)
- [시스템 아키텍처](./concepts/architecture.md)
- [데이터 타입 및 직렬화](./concepts/data-types.md)
- [노드 생명주기](./concepts/lifecycle.md)

### [개발 가이드](./guides/)
- [기본 노드 개발](./guides/basic-node-development.md)
- [고급 기능](./guides/advanced-features.md)
- [테스트 가이드](./guides/testing.md)
- [성능 최적화](./guides/performance-optimization.md)

### [API 레퍼런스](./api-reference/)
- [CustomNode 클래스](./api-reference/custom-node-class.md)
- [NodeSchema](./api-reference/node-schema.md)
- [직렬화 설정](./api-reference/serialization.md)

### [예제 코드](./examples/)
- [데이터 처리 노드](./examples/data-processing-node.py)
- [ML 학습 노드](./examples/ml-training-node.py)
- [API 연동 노드](./examples/api-integration-node.py)
- [스트리밍 처리 노드](./examples/streaming-node.py)

### [문제 해결](./troubleshooting/)
- [FAQ 및 일반적인 문제](./troubleshooting/faq.md)

## 빠른 시작

### 1. 설치

```bash
pip install ai-canvas-sdk
```

### 2. 첫 번째 노드 생성

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

### 3. 노드 실행

```bash
ai-canvas-sdk test hello_world.py
```

#### 주요 옵션

| 옵션 | 단축 | 설명 |
|------|------|------|
| `node_file` | | (필수) 테스트할 노드 파일 경로 |
| `--class` | | 특정 노드 클래스 지정 (파일에 여러 노드가 있을 경우) |
| `--validate-only` | | 스키마 검증만 수행, 실행하지 않음 |
| `--input` | `-i` | 입력 데이터 파일 경로 (JSON 또는 CSV) |
| `--params` | `-p` | 파라미터 JSON 문자열 |
| `--output` | `-o` | 결과를 저장할 파일 경로 (JSON 또는 CSV) |
| `--verbose` | `-v` | 상세 출력 모드 |

#### 활용 예시

**스키마 검증만 수행:**
```bash
ai-canvas-sdk test hello_world.py --validate-only
```

**입력 데이터를 지정하여 실행:**
```bash
ai-canvas-sdk test hello_world.py -i input_data.json
```

**파라미터 전달:**
```bash
ai-canvas-sdk test hello_world.py -p '{"message": "Hello"}'
```

**결과를 파일로 저장:**
```bash
ai-canvas-sdk test hello_world.py -i input_data.csv -o result.json
```

**특정 클래스를 지정하여 실행:**
```bash
ai-canvas-sdk test my_nodes.py --class MyCustomNode
```

**여러 옵션 조합:**
```bash
ai-canvas-sdk test hello_world.py -i data.json -p '{"threshold": 0.5}' -o output.csv -v
```

#### 입력 데이터 형식

- **JSON (포트별 매핑):** `{"port_label": [{"col": "val"}, ...]}` — 각 포트에 데이터를 개별 매핑
- **JSON (단일 배열):** `[{"col": "val"}, ...]` — 첫 번째 입력 포트에 자동 할당
- **CSV:** 첫 번째 입력 포트에 자동 할당

## 핵심 장점

### 서버 코드 격리
- AI Canvas 내부 서버 구조를 알 필요 없음
- gRPC 통신과 직렬화는 SDK가 자동 처리
- 비즈니스 로직에만 집중

### 데이터 처리 원칙
- Parquet/Arrow 기반 직렬화로 효율적 전송
- 대용량 데이터(파일/데이터셋)는 공유 볼륨으로 I/O하며, SDK/플랫폼은 파일 경로(예: `file:///data/...`)만 교환
- gRPC는 메타데이터와 실행 이벤트(로그/진행률/부분결과) 스트리밍을 담당

### 공유 볼륨(Local) 전용 구성

- 마운트: DAG 워커와 custom-node-runtime 컨테이너 모두 동일 경로(예: `/data`)로 공유 볼륨을 마운트합니다.
- 경로 전달: gRPC로는 파일 바이트를 보내지 않고, `file:///data/...` 형태의 경로만 교환합니다.
- 네임스페이스: 실행 단위 디렉터리 구조를 권장합니다. 예) `/data/{canvas_id}/{node_id}/{run_id}/...`
- 원자성: 임시 파일에 기록 후 `rename`으로 커밋하여 부분 읽기를 방지합니다.
- 권한: POSIX 권한/그룹을 사용해 최소 권한 원칙을 적용합니다(예: 770). rootless 컨테이너 권장.
- 용량/정리: 실행 종료 후 TTL/GC 정책으로 디스크를 정리합니다.

### 타입 안전성
- 런타임 스키마 검증(Pydantic/Protobuf)
- 선택적 mypy로 정적 타입 점검
- 런타임 타입 불일치 방지

## 배포/등록

- external_grpc 노드로 등록 시, 런타임이 gRPC로 실행합니다. 노드 매니페스트 예시:

```json
{
  "name": "partnerKeywordExtract",
  "version": "1.0.0",
  "execution_kind": "external_grpc",
  "runtime": {
    "endpoint": "dns:///custom-node-runtime:8443",
    "tls": true,
    "timeout_sec": 300,
    "streaming": true
  },
  "io": {
    "inputs_schema_ref": "schema://.../inputs.json",
    "outputs_schema_ref": "schema://.../outputs.json"
  }
}
```

배포(등록):

```bash
ai-canvas-sdk publish manifest.json
```

등록 즉시 사용 가능하며, 워커는 최신 레지스트리를 조회합니다(캐시 무효화 이벤트/TTL 적용).

## 실행 제어(취소/타임아웃/멱등성)

- **취소**: 플랫폼의 취소 요청이 gRPC Cancel(run_id)로 전달됩니다.
- **타임아웃**: 런타임이 작업 컨테이너/잡을 강제 종료합니다.
- **멱등성**: idempotency_key로 중복 실행을 방지합니다.

## 보안

- 모든 gRPC 통신은 mTLS를 사용합니다.
- 대용량 데이터는 공유 볼륨에서 최소 권한(경로 ACL/권한)으로 접근합니다.
- 런타임과 노드 이미지는 서명/스캔 정책을 따릅니다.


---

**다음 단계**: [설치 가이드](./getting-started/installation.md)에서 개발 환경을 설정해보세요.