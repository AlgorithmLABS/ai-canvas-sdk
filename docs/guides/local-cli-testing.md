# 로컬 CLI 테스트

`ai-canvas-sdk test` 로 커스텀 노드를 백엔드 없이 검증합니다. 이 명령은 노드 `.py` 를 import 하고, `get_schema()` 를 검사한 뒤 `run()` 을 직접 호출합니다. gRPC Custom Node Server, Secret Store, 캔버스 등록과는 무관합니다.

## 명령

```bash
ai-canvas-sdk test <node.py> [options]
```

| 옵션 | 단축 | 기본 | 동작 |
|------|------|------|------|
| `node_file` | | (필수) | CustomNode 서브클래스가 정의된 `.py` |
| `--class NAME` | | 파일의 첫 번째 노드 클래스 | 여러 클래스일 때 선택 |
| `--validate-only` | | off | 스키마만 검사하고 종료 |
| `--input PATH` | `-i` | 빈 DataFrame | JSON 또는 CSV |
| `--params JSON` | `-p` | 스키마 `Parameter.value` | `{"name": value}` |
| `--secret KEY=VALUE` | `-s` | 없음 | `ctx.get_secret` 주입. 반복 가능 |
| `--output PATH` | `-o` | stdout 표만 | `.json` 또는 `.csv` |
| `--verbose` | `-v` | 스키마 경고 숨김 | 경고 출력. 실행 실패 시 traceback |

설치 확인:

```bash
ai-canvas-sdk --version
```

출력은 버전 문자열 한 줄입니다.

## 최소 사이클

저장소 예제 기준:

```bash
ai-canvas-sdk test docs/examples/hello_node.py --validate-only

ai-canvas-sdk test docs/examples/hello_node.py \
  -i docs/examples/hello_input.json \
  -p '{"greeting": "Hi"}' \
  -o /tmp/hello_out.json \
  -v
```

성공 시 stdout 에 `Result: VALID`, 입력 행 수, `Test completed successfully!` 가 나오고, `ctx.log_info` / `ctx.progress` 는 stderr 에 붙습니다.

`-i` 를 빼면 빈 DataFrame 으로 `run()` 합니다. 입력 컬럼이 필요한 노드는 여기서 실패하는 것이 정상입니다.

## 입력 JSON

포트 레이블이 키입니다.

```json
{
  "input_data": [
    {"name": "Ada", "score": 91},
    {"name": "Grace", "score": 88}
  ]
}
```

여러 입력 포트:

```json
{
  "customer_info": [{"customer_id": "c1", "name": "Ada"}],
  "purchase_history": [{"customer_id": "c1", "amount": 120}]
}
```

- 리스트 → DataFrame 행
- 객체 하나 → 1행 DataFrame
- 그 외 JSON 값 → 그대로 `inputs[key]` 에 전달
- 최상위가 배열이면 첫 번째 입력 포트에 할당
- CSV 도 첫 번째 입력 포트에 할당

`run()` 이 받는 키는 포트 **`label`** 입니다. 파라미터 키는 `Parameter.name` 입니다 (`text` 는 UI 표시명).

## 파라미터

```bash
ai-canvas-sdk test filter_node.py -i scores.json -p '{"column":"score","threshold":90,"op":"gte"}'
```

`-p` 에 없는 이름은 스키마 `Parameter.value` 로 채워집니다. `value` 가 `None` 이면 채우지 않습니다.

## Secret

CLI 는 Secret Store 를 읽지 않습니다. `-s` 로 준 값만 `ctx.get_secret(name)` 에 들어갑니다.

```bash
ai-canvas-sdk test weather_node.py -s weather_api_key=local-test-key
ai-canvas-sdk test weather_node.py -s "weather_api_key=$WEATHER_API_KEY"
```

값을 안 넣고 `get_secret()` 을 호출하면 `SecretNotAvailableError` 입니다. 자세한 선언 규칙은 [Secret 사용 가이드](./using-secrets.md).

## 출력

- 터미널: 포트별 DataFrame head (최대 10행) 또는 repr
- `-o out.json`: 모든 포트를 JSON 으로. DataFrame 은 records
- `-o out.csv`: **첫 번째 DataFrame 포트만**. DataFrame 이 없으면 에러

## 클래스 탐색 규칙

- 해당 파일에서 정의된 `CustomNode` 서브클래스만 대상 (import 한 클래스는 제외)
- 여러 개면 첫 번째를 쓰고 `--class` 안내를 출력
- 로드 실패 / 스키마 invalid / `run()` 예외 → exit code 1

## 코드에서 직접 호출

`ai_canvas_sdk.testing` 모듈은 없습니다. 로컬에서 함수처럼 돌리려면 `NodeContext` 를 직접 만듭니다.

```python
import pandas as pd
from ai_canvas_sdk import NodeContext
from hello_node import HelloWorldNode

ctx = NodeContext(
    execution_id="local-test",
    node_id="HelloWorld",
    secrets={},  # get_secret 을 쓰면 여기에 이름=값
)
node = HelloWorldNode()
result = node.run(
    inputs={"input_data": pd.DataFrame([{"name": "Ada"}])},
    parameters={"greeting": "Hi"},
    ctx=ctx,
)
print(result["output_data"])
```

## 이 CLI가 검증하지 않는 것

- 캔버스 UI / 포트 연결
- 백엔드 등록 (`register` 는 별도 명령, [CI 가이드](../ci/README.md))
- Secret Store 에 저장된 실제 값
- gRPC 직렬화 경로 (`DataSerializer`, 3MB 제한, 공유 볼륨)
- `ctx.is_cancelled()` — 테스트 컨텍스트는 항상 `False`

플랫폼에서 한 번 더 실행해야 위 항목을 확인할 수 있습니다.
