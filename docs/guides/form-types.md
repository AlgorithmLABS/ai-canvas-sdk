# form_type (캔버스 위젯)

`Parameter.form_type` 은 파이썬 타입이 아니라 **프론트 `forms` 레지스트리 키**입니다. 캔버스는 이 문자열로 위젯을 고르고, 키가 없으면 오른쪽 탭에 `formType undefined` 를 그립니다.

프론트 소스: `ai_canvas_front/packages/elements/src/types/formType.ts` 의 `FORM_TYPES`, `packages/elements/src/forms/index.tsx` 의 `forms`.

## 없는 값 (이 때문에 깨짐)

다음 문자열은 **등록되어 있지 않습니다.**

- `number` — `sample_filter` 의 `formType undefined` 원인. 숫자는 `numCount` 또는 `slider` (간단한 값은 `input`)
- `text`, `integer`, `float`, `checkbox`, `dropdown`

## 커스텀 노드에서 쓸 것

| `form_type` | 용도 | `options` |
|-------------|------|-----------|
| `input` | 한 줄 텍스트/숫자 입력 | `{"run": true, "min": 0, "max": 100}` (선택) |
| `textarea` | 여러 줄 텍스트 | |
| `numCount` | 숫자 스피너 | `{"min": 0, "max": 100, "step": 1}` |
| `slider` | 슬라이더 | `numCount` 와 동일 + `showMaxLabelOnMaxValue` |
| `bool` | 토글 | |
| `select` | 드롭다운 | `{"selectOption": [{"text": "이상", "value": "gte"}]}` |
| `radioSelect` | 라디오 | select 와 유사 |
| `multiSelect` | 다중 선택 | |
| `multiInput` | 여러 입력 | |
| `dateSelect` | 날짜 | `{"type": "date"}` 또는 `"datetime-local"` |
| `columnSelect` | 연결 DATASET 의 컬럼 하나 | `{"datasetPortLabel": "data_in"}` |
| `multiColumnSelect` | 컬럼 여러 개 | |
| `minMax` | 최소/최대 쌍 | |
| `doubleInput` | 입력 두 칸 | `{"firstLabel": "min", "secondLabel": "max"}` |

`select` 의 옵션 키는 **`selectOption`** 입니다. `items` 가 아닙니다. 각 항목은 `text` + `value`.

숫자 예:

```python
Parameter(
    text="임계값",
    name="threshold",
    form_type="numCount",
    value=90,
    is_tab=True,
    options={"min": 0, "max": 100, "step": 1},
)
```

`is_tab=True` 가 있어야 오른쪽 파라미터 탭에 보입니다. 생략하면 위젯 종류와 무관하게 캔버스에 안 나옵니다.

## 레지스트리 전체 (undefined 가 안 나는 키)

프론트 `FORM_TYPES` 와 `forms` 객체 키는 아래와 같습니다. 여기 없는 문자열은 `formType undefined` 입니다.

`input`, `select`, `upload`, `radioSelect`, `bool`, `minMax`, `titleForm`, `accordion`, `multiSelect`, `slider`, `numCount`, `featureByFeature`, `columnSelect`, `multiColumnSelect`, `sampleDataForm`, `modeSelect`, `chartColorSelect`, `portLabelUpdater`, `customizeForm`, `runButton`, `columnTagEditor`, `imageInput`, `filterEditor`, `chartColumnSelect`, `addItemOption`, `colorSelect`, `doubleSelect`, `tabUpdater`, `columnFormatSelect`, `formatSelect`, `addAnnotationLabel`, `fontStyleSelect`, `customNameUpdater`, `multiInput`, `textarea`, `applicationShareUpdater`, `dateSelect`, `chatPromptMaker`, `dropdownEditor`, `targetNodeSelector`, `portEditor`, `doubleInput`

아래는 캔버스 코어 노드용이라 커스텀 노드에서는 쓰지 않는 것이 좋습니다.

`runButton`, `portLabelUpdater`, `portEditor`, `tabUpdater`, `customNameUpdater`, `applicationShareUpdater`, `targetNodeSelector`, `chatPromptMaker`, `sampleDataForm`, `titleForm`, `accordion`, `featureByFeature`, `filterEditor`, `chartColumnSelect`, `chartColorSelect`, `columnFormatSelect`, `formatSelect`, `fontStyleSelect`, `addAnnotationLabel`, `addItemOption`, `dropdownEditor`, `customizeForm`, `modeSelect`

CLI `ai-canvas-sdk test` 는 `form_type` 을 검사하지 않습니다. 잘못된 값은 캔버스 UI 에서만 드러납니다.
