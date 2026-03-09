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

## 빠른 시작

### 1. 설치

```bash
pip install "git+https://github.com/AlgorithmLABS/ai-canvas-sdk"
```

### 2. 첫 번째 노드 생성

```python
from ai_canvas_sdk import CustomNode, NodeSchema, PortType, NodeContext

class HelloWorldNode(CustomNode):
  @staticmethod
  def get_schema() -> NodeSchema:
    return NodeSchema(
      name="HelloWorld",
      display_name="Hello World",
      description="간단한 Hello World 노드",
      inputs=[{"name": "input_text", "type": PortType.TEXT}],
      outputs=[{"name": "output_text", "type": PortType.TEXT}],
    )

  def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
    text = inputs.get("input_text", "World")
    ctx.log_info("processing hello")
    ctx.progress(0.5)
    return {"output_text": f"Hello, {text}!"}
```

### 3. 노드 실행

```bash
ai-canvas-sdk run hello_world.py --test
```

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


## 실행 제어(취소/타임아웃/멱등성)

- **취소**: 플랫폼의 취소 요청이 gRPC Cancel(run_id)로 전달됩니다.
- **타임아웃**: 런타임이 작업 컨테이너/잡을 강제 종료합니다.
- **멱등성**: idempotency_key로 중복 실행을 방지합니다.

## 보안

- 모든 gRPC 통신은 mTLS를 사용합니다.
- 대용량 데이터는 공유 볼륨에서 최소 권한(경로 ACL/권한)으로 접근합니다.
- 런타임과 노드 이미지는 서명/스캔 정책을 따릅니다.


