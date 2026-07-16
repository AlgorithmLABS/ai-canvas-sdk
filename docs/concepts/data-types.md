# 데이터 타입 및 직렬화

Custom Node가 포트로 주고받는 데이터 타입과, 그 데이터가 노드 사이에서 어떻게 전달되는지를 설명합니다.

핵심은 두 가지 관심사를 분리하는 것입니다.

- **노드 작성자가 다루는 것**: `run()` 안에서 만지는 평범한 Python 객체(대부분 `pandas.DataFrame`).
- **플랫폼/SDK가 대신 처리하는 것**: 그 객체를 노드 사이로 실어 나르는 직렬화·전송.

노드를 개발할 때 직렬화 코드를 직접 작성할 일은 거의 없습니다. 신경 써야 하는 것은 각 포트의 **연결 타입(`port_type`)** 을 올바르게 고르는 일뿐입니다.

## 포트 데이터 타입 (`PortTypeEnum`)

포트의 데이터 타입은 `PortTypeEnum`으로 지정합니다. 이 값은 "값을 어떻게 직렬화할지"가 아니라 **캔버스에서 이 포트를 어떤 포트와 연결할 수 있는지**를 알려주는 연결 타입입니다.

```python
from ai_canvas_sdk import PortTypeEnum
```

| `PortTypeEnum` 값 | 흐르는 Python 타입 | 설명 |
|---|---|---|
| `DATASET` (`"dataset"`) | `pandas.DataFrame` | 테이블 형태 데이터. 노드 간 연결의 **사실상 표준**입니다. |
| `UNTRAINED` (`"untrainedModel"`) | 모델 객체/구성 | 아직 학습되지 않은 ML 모델. |
| `TRAINED` (`"trainedModel"`) | 모델 객체 | 학습이 끝난 ML 모델. |
| `TRANSFORMER` (`"transformer"`) | 변환기 객체 | 전처리·변환기(스케일러, 인코더 등). |
| `DISPLAY` (`"display"`) | `dict` / `list` / 스칼라 | 노드 화면에 표시하기 위한 데이터. **다음 노드로 체이닝되지 않습니다.** |

`port_type`을 올바르게 고르는 일이 중요한 이유는, 이 값이 캔버스에게 **이 출력이 어떤 입력으로 이어질 수 있는지**를 알려주기 때문입니다. 예를 들어 `TRAINED` 출력 포트는 학습된 모델을 입력으로 받는 추론 노드에만 연결됩니다. 타입이 맞지 않는 포트끼리는 캔버스에서 연결선이 그어지지 않습니다.

> 현재 대부분의 노드는 `DATASET`(=`pandas.DataFrame`)만으로 파이프라인을 구성합니다. 모델·변환기 타입은 학습/추론 노드를 나눌 때 사용합니다.

## 노드 작성자가 다루는 데이터

노드의 `run()`은 항상 아래 형태입니다.

```python
def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
    df = inputs["input_data"]          # 입력 포트 label을 key로 하는 dict
    result = df.copy()
    # ... 비즈니스 로직 ...
    return {"output_data": result}      # 출력 포트 label을 key로 하는 dict
```

- `inputs`: **입력 포트의 `label`을 key로 하는 dict**. 값은 보통 `pandas.DataFrame`입니다.
- 반환값: **출력 포트의 `label`을 key로 하는 dict**. `PortTypeEnum.DATASET` 포트라면 값은 `DataFrame`입니다.

즉 노드 작성자는 바이트·버퍼·직렬화 포맷을 다루지 않고, 평범한 Python 객체만 주고받으면 됩니다. 포트의 `label`과 `port_type`을 스키마에 선언하는 방법은 [Custom Node 클래스 레퍼런스](../api-reference/custom-node-class.md)를 참고하세요.

## 직렬화는 플랫폼이 처리합니다

노드 사이의 데이터 전송·직렬화는 **SDK와 플랫폼이 자동으로** 처리합니다. 노드 작성자가 관여할 필요가 없습니다.

- `DataFrame`은 **Parquet/Arrow** 기반으로 전송됩니다.
- 대용량 데이터는 DAG 워커와 노드 런타임이 함께 마운트한 **공유 볼륨**을 통해 오갑니다. 이때 gRPC로는 파일 바이트가 아니라 `file:///data/...` 형태의 **경로만** 교환됩니다.
- 취소·타임아웃 같은 실행 제어도 플랫폼이 gRPC로 담당합니다.

공개 직렬화 헬퍼로 `DataSerializer` 하나가 존재합니다.

```python
from ai_canvas_sdk import DataSerializer
```

다만 이것은 SDK 내부와 저수준 통합을 위한 도구이며, **일반적인 노드는 이 클래스를 직접 호출하지 않습니다.** `run()`에서 `pandas.DataFrame`을 받고 반환하는 것으로 충분합니다.

이러한 경계 덕분에 노드 작성자는 서버 내부 구조나 전송 포맷을 몰라도 되고, 비즈니스 로직에만 집중할 수 있습니다. 전체 데이터 흐름과 공유 볼륨 구조는 [아키텍처 문서](./architecture.md)에서 더 자세히 다룹니다.

## 관련 문서

- [Custom Node 클래스 레퍼런스](../api-reference/custom-node-class.md) — 포트·스키마·`run()` 시그니처
- [아키텍처](./architecture.md) — gRPC 통신, 공유 볼륨, 데이터 흐름
