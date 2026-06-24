# Secret 사용 가이드

커스텀 노드가 API 키·토큰 같은 **비밀 값**을 코드에 하드코딩하지 않고 안전하게 사용하는 방법을 설명합니다.

## 개요

외부 API를 호출하는 노드는 보통 API 키가 필요합니다. 이 값을 노드 소스 코드에 직접 적으면:

- 소스 코드를 보는 모든 사람에게 키가 노출됩니다.
- 키를 교체할 때마다 노드를 다시 작성·재등록해야 합니다.

Custom Node SDK는 이를 해결하기 위해 **secret 선언/주입 메커니즘**을 제공합니다. 노드는 **필요한 secret의 이름만** 선언하고, **실제 값은 플랫폼 관리자가 Secret Store에 등록**합니다. 실행 시점에 플랫폼이 선언된 secret만 노드 컨텍스트로 주입하고, 노드는 `ctx.get_secret(name)`으로 꺼내 씁니다.

## 전체 흐름

```
① 선언               ② 등록(관리자)            ③ 주입(플랫폼)         ④ 소비(노드)
┌────────────┐      ┌──────────────┐        ┌──────────────┐      ┌──────────────┐
│ required_   │      │ Secret Store │        │ 선언된 이름의 │      │ ctx.get_     │
│ secrets =   │─등록→│ 에 값 저장    │──실행시─→│ secret 값만   │──────→│ secret(name) │
│ ["api_key"] │ 요청 │ (admin 전용)  │        │ 컨텍스트 주입 │      │ → 값 사용     │
└────────────┘      └──────────────┘        └──────────────┘      └──────────────┘
   노드 코드            플랫폼 관리자             플랫폼 런타임           노드 코드
```

- **노드 개발자**가 하는 일: ①, ④ (이름 선언 + 값 소비)
- **플랫폼 관리자**가 하는 일: ② (값 등록·교체·삭제)
- **플랫폼**이 자동으로 하는 일: ③ (선언된 secret만 골라서 주입)

> 핵심: **노드 코드에는 이름만, 값은 Secret Store에만** 존재합니다. 값은 노드 소스/메타데이터/로그 어디에도 저장되지 않습니다.

## ① 노드에서 secret 선언

`CustomNode` 클래스 속성 `required_secrets`에 필요한 secret 이름을 선언합니다.

```python
from ai_canvas_sdk import CustomNode, NodeContext, NodeSchema, NodeData, Port, PortEnum, PortTypeEnum, PositionEnum


class WeatherNode(CustomNode):
    # 이 노드가 요구하는 secret 이름 목록
    required_secrets = ["weather_api_key"]

    def get_schema(self) -> NodeSchema:
        ...
```

- 반드시 **클래스 속성 리터럴**(문자열 리스트)로 작성하세요. 노드 등록 시 SDK가 소스를 실행하지 않고 **정적(AST)으로** 이 값을 추출해 노드 메타데이터에 저장합니다.
- 동적 계산(`required_secrets = build_names()`)이나 `__init__` 안에서 설정(`self.required_secrets = [...]`)하면 추출되지 않습니다.
- 여기에 선언한 이름만 실행 시 주입됩니다. 선언하지 않은 secret은 `ctx.get_secret()`으로 접근할 수 없습니다.

## ② Secret Store에 값 등록 (플랫폼 관리자)

값 등록·교체·삭제는 **플랫폼 관리자만** 수행합니다. 노드 개발자는 자신이 선언한 secret **이름**(예: `weather_api_key`)을 관리자에게 전달하고 등록을 요청하면 됩니다.

관리자는 AI Canvas 관리자 화면(또는 백엔드 Admin API)에서 custom-node secret을 등록합니다. 등록 시점은 노드 등록 전후 어느 쪽이든 무방하며, **노드 실행 전까지 등록되어 있으면** 됩니다.

> 노드 개발자 입장에서 ②는 코드 작업이 아닙니다. 등록이 아직 안 된 secret을 `get_secret()`으로 꺼내면 `SecretNotAvailableError`가 발생합니다 — 이 경우 관리자에게 등록을 요청하세요.

## ③ 노드에서 소비

`run()`의 실행 컨텍스트 `ctx`에서 `get_secret(name)`으로 값을 가져옵니다. 반환값은 항상 `str`입니다.

```python
def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
    api_key = ctx.get_secret("weather_api_key")  # required_secrets 에 선언 + 관리자 등록 시 성공
    # ... api_key 로 외부 API 호출 ...
    return {"output_data": result}
```

- 선언하지 않았거나(미주입) 등록되지 않은 경우 `SecretNotAvailableError`가 발생합니다.
- secret 값은 필요한 순간에만 꺼내 쓰고, 인스턴스 속성 등에 오래 보관하지 마세요.

## 완전한 예시

```python
import pandas as pd
import requests

from ai_canvas_sdk import (
    CustomNode, NodeContext, NodeSchema, NodeData,
    Port, PortEnum, PortTypeEnum, PositionEnum,
)


class WeatherNode(CustomNode):
    """입력된 도시 목록의 현재 기온을 외부 API로 조회하는 노드."""

    required_secrets = ["weather_api_key"]

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="Weather",
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="cities",
                    ),
                ],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="weather",
                    ),
                ],
            ),
            version="1.0.0",
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        api_key = ctx.get_secret("weather_api_key")
        df = inputs["cities"].copy()

        ctx.log_info(f"기온 조회 시작: {len(df)}개 도시")  # 값이 아닌 메타데이터만 로그
        temps = []
        for i, city in enumerate(df["city"]):
            resp = requests.get(
                "https://api.example.com/weather",
                params={"q": city, "appid": api_key},
                timeout=10,
            )
            temps.append(resp.json()["temp"])
            ctx.progress((i + 1) / len(df))

        df["temp"] = temps
        return {"weather": df}
```

## 로컬 테스트

`get_secret()`을 쓰는 노드는 `ai-canvas-sdk test` CLI의 `--secret`/`-s KEY=VALUE` 옵션으로 secret을 주입해 검증합니다(여러 번 지정 가능).

```bash
ai-canvas-sdk test weather_node.py -s weather_api_key=local-test-key
```

secret을 주입하지 않고 `get_secret()` 노드를 실행하면 `SecretNotAvailableError`가 발생합니다. 테스트용 키는 코드에 커밋하지 말고 셸 환경 변수 등에서 읽어 전달하는 것을 권장합니다.

```bash
ai-canvas-sdk test weather_node.py -s "weather_api_key=$WEATHER_API_KEY"
```

CLI 없이 코드에서 직접 검증하려면, `secrets`를 채운 `NodeContext`를 만들어 `run()`을 호출하면 됩니다.

```python
from ai_canvas_sdk import NodeContext
from my_node import WeatherNode
import pandas as pd

ctx = NodeContext(
    execution_id="local-test",
    node_id="weather",
    secrets={"weather_api_key": "테스트용-키"},  # 로컬 검증용 값 직접 주입
)

node = WeatherNode()
result = node.run(
    inputs={"cities": pd.DataFrame({"city": ["Seoul", "Tokyo"]})},
    parameters={},
    ctx=ctx,
)
print(result["weather"])
```

## 보안 주의사항

- **secret 값을 로그로 출력하지 마세요.** `ctx.log_info(api_key)`, `print(api_key)` 등은 값이 실행 로그에 남아 유출됩니다. 로그에는 secret **이름**만 남기세요.
- secret 값을 출력 포트 데이터(반환 `dict`)에 그대로 담지 마세요. 다음 노드와 화면에 노출됩니다.
- `required_secrets`에는 **실제로 사용하는 secret만** 선언하세요. 플랫폼은 선언된 것만 주입합니다.

## 자주 발생하는 오류

### `SecretNotAvailableError`

`ctx.get_secret(name)`이 던지는 예외입니다. 예외 메시지에는 secret 이름만 포함되고 값은 포함되지 않습니다.

| 원인 | 해결 |
|---|---|
| `required_secrets`에 이름을 선언하지 않음 | 클래스 속성 `required_secrets`에 이름 추가 후 노드 재등록 |
| `required_secrets`를 리터럴이 아닌 동적/인스턴스 속성으로 작성 | 클래스 속성 리터럴(`required_secrets = ["..."]`)로 변경 후 재등록 |
| 관리자가 Secret Store에 아직 등록하지 않음 | 플랫폼 관리자에게 해당 secret 등록 요청 |
| 로컬 CLI(`ai-canvas-sdk test`)로 실행 시 미주입 | `--secret KEY=VALUE` 로 주입 (위 [로컬 테스트](#로컬-테스트) 참고) |

---

**관련 문서**: [CustomNode 클래스 API 레퍼런스](../api-reference/custom-node-class.md) · [기본 노드 개발 가이드](./basic-node-development.md)
