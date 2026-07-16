# 노드 생명주기

커스텀 노드가 **작성·등록되어 실행되고 결과를 돌려주기까지** 거치는 단계를 설명합니다. 여기서 다루는 것은 노드 개발자가 실제로 손대는 표면뿐입니다. 직렬화·재시도·리소스 제한·타임아웃 같은 나머지는 모두 **플랫폼이 책임**지며, 노드 코드는 관여하지 않습니다.

## 흐름 개요

```
작성/등록  →  실행 준비          →  validate(선택)  →  run 실행       →  결과 직렬화
(스키마+로직) (ctx 주입·입력 역직렬화)  (입력 사전 검증)   (ctx.* 사용)    (다음 노드/화면으로)
```

각 단계에서 개발자가 만지는 것과 플랫폼이 알아서 하는 것을 구분하는 것이 핵심입니다.

## 1. 작성 / 등록

개발자는 `CustomNode`를 상속해 두 가지를 구현합니다.

- `get_schema(self) -> NodeSchema` — 노드의 이름, 입출력 포트, 파라미터 등 **스키마**(`@staticmethod`가 아닌 인스턴스 메서드).
- `run(self, inputs, parameters, ctx) -> dict` — 실제 **처리 로직**.

파일 맨 끝에 `node = MyNode()` 인스턴스를 하나 만들어 두면, SDK가 이 인스턴스를 노드로 인식합니다.

등록 시 SDK는 스키마와 함께 `required_secrets`(클래스 속성 리터럴)를 **AST로 정적 추출**해 메타데이터로 수집합니다. 소스를 실행하지 않고 읽기만 하므로, `required_secrets`는 반드시 클래스 속성 리터럴이어야 합니다(자세한 내용은 [Secret 사용 가이드](../guides/using-secrets.md)). 로컬 검증은 `ai-canvas-sdk test <file.py>`로, 플랫폼 등록/배포는 별도 도구(CI push 경로)로 수행합니다.

## 2. 실행 준비 (플랫폼 담당)

플랫폼이 실행 단위마다 다음을 준비해 노드에 넘겨줍니다.

- **`NodeContext` 주입**: `execution_id`, `node_id`, 선언된 secret 등을 담은 컨텍스트를 만들어 `run()`의 `ctx`로 전달합니다.
- **입력 역직렬화**: 이전 노드가 넘긴 포트 데이터를 역직렬화해 `inputs` dict로 전달합니다. 키는 입력 포트의 `label`, 값은 보통 `pandas.DataFrame`입니다(예: `inputs["input_data"]`).

Parquet/Arrow 직렬화·역직렬화와 공유 볼륨 파일 경로 교환은 전부 플랫폼이 처리합니다. 노드는 그냥 `DataFrame`을 받고 `DataFrame`을 반환할 뿐, 직렬화 코드를 쓰지 않습니다.

## 3. 검증 (선택)

노드에 `validate(self, inputs, parameters) -> None`을 구현했다면, 플랫폼이 `run()` **이전에** 호출합니다. 잘못된 입력을 조기에 막는 용도이며, 구현은 선택 사항입니다.

```python
def validate(self, inputs: dict, parameters: dict) -> None:
    df = inputs["input_data"]
    if "name" not in df.columns:
        raise ValueError("'name' 컬럼이 필요합니다")  # 검증 실패는 ValueError/TypeError로
```

검증 실패는 `ValueError` 또는 `TypeError`로 알립니다. 별도의 커스텀 예외 클래스를 만들 필요가 없습니다.

## 4. 실행

플랫폼이 `run(self, inputs, parameters, ctx)`를 호출합니다. 이 안에서 개발자는 `ctx`를 통해 실행 환경과 상호작용합니다.

- `ctx.log_info(msg)` / `log_debug` / `log_warning` / `log_error` / `log_critical` — 로그 (인자는 문자열 메시지 하나).
- `ctx.progress(pct)` — 0.0~1.0 사이 진행률 보고 (범위 밖이면 `ValueError`).
- `ctx.is_cancelled()` — 취소 요청 여부 확인 (협조적 취소, 아래 6단계 참고).
- `ctx.get_secret(name)` — `required_secrets`에 선언되고 주입된 secret 값. 없으면 `SecretNotAvailableError`.

반환값은 **출력 포트 `label`을 키로 하는 dict**입니다(예: `{"output_data": df}`).

## 5. 결과 반환 (플랫폼 담당)

`run()`이 반환한 dict를 플랫폼이 직렬화해 다음 노드의 입력이나 화면 표시로 전달합니다. 여기서도 직렬화·전송은 전부 플랫폼 몫입니다.

## 6. 취소 / 타임아웃 (플랫폼 담당)

취소와 타임아웃은 플랫폼이 gRPC로 관리합니다. 노드가 할 일은 **협조적 취소**뿐입니다. 즉, 오래 도는 루프 안에서 `ctx.is_cancelled()`를 주기적으로 확인해 스스로 조기 종료하는 것입니다. 재시도, 리소스 제한, 강제 종료 같은 것은 플랫폼 책임이며 노드 API가 아닙니다.

## 한눈에 보는 최소 예제

각 `ctx.*` 호출이 생명주기의 어느 지점에 놓이는지 보여 줍니다.

```python
import pandas as pd
from ai_canvas_sdk import (
    CustomNode, NodeContext, NodeData, NodeSchema,
    Parameter, Port, PortEnum, PortTypeEnum, PositionEnum,
)


class GreetingNode(CustomNode):
    """입력 데이터프레임에 인사말 컬럼을 추가하는 노드."""

    def get_schema(self) -> NodeSchema:  # 1. 스키마
        return NodeSchema(
            name="Greeting",
            data=NodeData(
                input_ports=[Port(
                    type=PortEnum.TARGET, position=PositionEnum.LEFT,
                    port_type=PortTypeEnum.DATASET, label="input_data",
                )],
                output_ports=[Port(
                    type=PortEnum.SOURCE, position=PositionEnum.RIGHT,
                    port_type=PortTypeEnum.DATASET, label="output_data",
                )],
                params=[Parameter(
                    text="인사말", name="greeting", form_type="input",
                    value="Hello", value_type="string", is_tab=True,
                )],
            ),
            version="1.0.0",
        )

    def validate(self, inputs: dict, parameters: dict) -> None:  # 3. 검증(선택)
        if "name" not in inputs["input_data"].columns:
            raise ValueError("'name' 컬럼이 필요합니다")

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:  # 4. 실행
        df = inputs["input_data"].copy()          # 2단계에서 주입·역직렬화된 입력
        greeting = parameters.get("greeting", "Hello")

        ctx.log_info(f"{len(df)}개 행에 인사말 추가")  # 로그
        ctx.progress(0.5)                            # 진행률
        if ctx.is_cancelled():                       # 협조적 취소
            return {"output_data": df}
        df["greeting"] = df["name"].map(lambda n: f"{greeting}, {n}!")
        ctx.progress(1.0)

        return {"output_data": df}                   # 5단계에서 직렬화됨


node = GreetingNode()
```

로컬에서 직접 호출해 볼 때는 `NodeContext`를 손수 만들어 주입합니다. `execution_id`와 `node_id`는 **필수 인자**이므로 무인자 `NodeContext()`는 `TypeError`로 즉시 깨집니다.

```python
ctx = NodeContext(execution_id="local-test", node_id="greeting")
result = node.run({"input_data": pd.DataFrame({"name": ["A", "B"]})}, {"greeting": "안녕"}, ctx)
```

secret을 쓰는 노드라면 `NodeContext(execution_id="local-test", node_id="greeting", secrets={"key": "..."})`처럼 값을 채워 만듭니다.

## 관련 문서

- [CustomNode 클래스 API 레퍼런스](../api-reference/custom-node-class.md) — `get_schema` / `run` / `validate`와 `ctx` 메서드 전체
- [Secret 사용 가이드](../guides/using-secrets.md) — `required_secrets` 선언과 `ctx.get_secret` 소비
- [아키텍처 개요](./architecture.md) — 플랫폼이 직렬화·실행·취소를 처리하는 구조
