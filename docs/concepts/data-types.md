# 데이터 타입 및 직렬화

노드 작성자가 다루는 타입은 포트 `PortTypeEnum` 과 `run()` 입출력입니다. gRPC 직렬화는 플랫폼이 `DataSerializer` 로 처리하며, **로컬 `ai-canvas-sdk test` 는 이 경로를 타지 않습니다.**

## PortTypeEnum

```python
from ai_canvas_sdk import PortTypeEnum

class PortTypeEnum(Enum):
    DATASET = "dataset"
    UNTRAINED = "untrainedModel"
    TRAINED = "trainedModel"
    TRANSFORMER = "transformer"
    DISPLAY = "display"
```

`from ai_canvas_sdk import PortType` 는 실패합니다. `JSON`, `DATAFRAME`, `TRANSFORMATION` 값도 없습니다.

| PortTypeEnum | 로컬 CLI에서 흔한 Python 값 | 비고 |
|--------------|-----------------------------|------|
| `DATASET` | `pandas.DataFrame` | CLI `-i` JSON/CSV 가 DataFrame 으로 들어옴 |
| `DISPLAY` | `dict` / `list` / 스칼라 | 체이닝보다 노드 UI 표시용 |
| `UNTRAINED` / `TRAINED` / `TRANSFORMER` | 객체 또는 경로 | 플랫폼 런타임 직렬화에 의존. CLI는 파일을 모델로 역직렬화하지 않음 |

요약 JSON 을 내고 싶으면 출력 포트를 `DISPLAY` 로 두거나, DATASET 컬럼으로 넣습니다.

## 로컬 test vs 플랫폼 직렬화

`ai-canvas-sdk test` 는 import 한 노드의 `run()` 에 DataFrame/dict 를 그대로 넘깁니다. Parquet/Arrow 변환은 없습니다.

캔버스에서 실행될 때 `DataSerializer` (`ai_canvas_sdk/serialization.py`) 가 DataFrame 을 gRPC `PortData` 로 바꿉니다.

| 행 수 | 전략 |
|-------|------|
| &lt; 10,000 | JSON |
| 10,000 이상, Arrow 페이로드 &lt; 3 MiB | Arrow + LZ4 |
| Arrow 페이로드 ≥ 3 MiB 또는 행이 매우 큼 | `ValueError` — 공유 볼륨 파일 경로 사용 |

상수:

- `SMALL_DATA_THRESHOLD = 10_000`
- `LARGE_DATA_THRESHOLD = 100_000`
- `GRPC_SIZE_LIMIT = 3 * 1024 * 1024`

대용량은 gRPC 바이트가 아니라 `file:///data/...` 경로로 넘기는 것이 플랫폼 설계입니다.

## run() 에서 DataFrame 다루기

```python
def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
    df = inputs["input_data"]          # DataFrame
    out = df.copy()
    return {"output_data": out}        # DataFrame 그대로
```

`Dataset(dataframe=df)` 래퍼는 없습니다.

DISPLAY 포트 예:

```python
return {
    "filtered": filtered_df,
    "summary": {"rows": int(len(filtered_df))},
}
```
