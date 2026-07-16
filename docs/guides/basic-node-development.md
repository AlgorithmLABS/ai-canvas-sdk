# 기본 노드 개발 가이드

커스텀 노드 개발의 핵심 패턴과 모범 사례를 상세히 설명합니다.

모든 예제는 실제 SDK 공개 API만 사용합니다. 노드가 지켜야 할 계약은 단 두 가지입니다.

- `get_schema(self) -> NodeSchema` — 노드의 포트와 파라미터를 정의하는 **인스턴스 메서드**.
- `run(self, inputs, parameters, ctx) -> dict` — 실제 실행 로직. 반환값은 **출력 포트 `label`을 키로 하는 dict**.

`get_schema`에서 정의한 포트의 `label`이 곧 `run`의 `inputs[label]` 키이자 반환 `dict`의 키입니다. 이 `label`이 스키마와 실행 코드를 잇는 유일한 계약입니다.

## 개발 원칙

### 1. 단일 책임 원칙
각 노드는 하나의 명확한 기능만 수행해야 합니다. 아래는 원칙을 보여주는 부분 예시입니다(`get_schema`는 지면상 생략).

```python
# 좋은 예: 단일 책임
class DataNormalizationNode(CustomNode):
    """수치 컬럼 정규화만 담당한다."""

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs["input_data"].copy()  # 원본 보호를 위해 복사
        numeric = df.select_dtypes("number")
        df[numeric.columns] = (numeric - numeric.min()) / (numeric.max() - numeric.min())
        return {"output_data": df}


# 나쁜 예: 여러 책임을 한 노드에
class DataProcessingMegaNode(CustomNode):
    """정규화 + 필터링 + 집계 + 시각화까지 전부..."""

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        # 하나가 실패하면 전체가 실패하고, 재사용도 테스트도 어렵다.
        ...
```

### 2. 명확한 인터페이스
입력과 출력을 명확히 정의합니다. 포트/파라미터는 전부 `data=NodeData(...)` 안에 넣으며, `NodeSchema`에는 `display_name`·`description`·`inputs`·`outputs`·`parameters` 같은 필드가 존재하지 않습니다.

```python
from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    NodeData,
    NodeSchema,
    Parameter,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
)


class WellDefinedNode(CustomNode):
    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="DataAggregator",
            category="custom",  # 관례상 "custom"
            version="1.0.0",
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,        # 입력 포트는 TARGET
                        position=PositionEnum.LEFT,  # 입력은 왼쪽에 배치(관례)
                        port_type=PortTypeEnum.DATASET,  # 표 형태 데이터는 DATASET
                        label="source_data",        # run()에서 inputs["source_data"]
                        required=True,
                    ),
                ],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,         # 출력 포트는 SOURCE
                        position=PositionEnum.RIGHT,  # 출력은 오른쪽에 배치(관례)
                        port_type=PortTypeEnum.DATASET,
                        label="aggregated_data",     # run()이 반환하는 dict의 키
                    ),
                ],
                params=[
                    Parameter(
                        text="그룹화 컬럼",           # 화면에 보이는 라벨
                        name="group_by",             # run()에서 parameters["group_by"]
                        form_type="input",
                        value="category",            # 기본값
                        value_type="string",
                        is_tab=True,                 # True 여야 파라미터 탭에 노출
                    ),
                ],
            ),
        )
```

## 기본 노드 구조

### 완전한 노드 템플릿

```python
import logging

import pandas as pd

from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    NodeData,
    NodeSchema,
    Parameter,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
)

# 모듈 레벨 로거. run() 내부에서는 ctx.log_* 를 우선 사용하고,
# 순수 헬퍼 함수 등에서는 이 로거를 쓴다.
logger = logging.getLogger(__name__)


class TemplateNode(CustomNode):
    """노드 개발 템플릿.

    노드는 보통 상태를 갖지 않는다(stateless). 실행마다 inputs/parameters/ctx만으로
    동작하도록 설계하면 재사용과 테스트가 쉬워진다. 상수가 필요하면 클래스 속성으로 둔다.
    """

    DEFAULT_THRESHOLD = 0.5

    def get_schema(self) -> NodeSchema:
        """노드 메타데이터 정의 — 포트와 파라미터는 전부 data=NodeData(...) 안에."""
        return NodeSchema(
            name="TemplateNode",
            category="custom",
            version="1.0.0",
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="input_data",
                        required=True,
                    ),
                ],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="processed_data",
                    ),
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DISPLAY,  # 화면 표시용 출력
                        label="summary",
                    ),
                ],
                params=[
                    Parameter(
                        text="임계값",
                        name="threshold",
                        form_type="number",
                        value=0.5,
                        value_type="number",
                        is_tab=True,
                    ),
                    Parameter(
                        text="집계 방법",
                        name="method",
                        form_type="select",
                        value="mean",
                        value_type="string",
                        options={
                            "items": [
                                {"label": "평균", "value": "mean"},
                                {"label": "중앙값", "value": "median"},
                                {"label": "최댓값", "value": "max"},
                            ]
                        },
                        is_tab=True,
                    ),
                ],
            ),
        )

    def validate(self, inputs: dict, parameters: dict) -> None:
        """입력 검증(선택적 관례). 잘못된 입력은 ValueError/TypeError로 알린다.

        validate는 ABC에 정의된 메서드가 아니라 관례다. 커스텀 예외 클래스를
        만들 필요 없이 표준 예외를 던지면 된다.
        """
        df = inputs.get("input_data")
        if df is None or df.empty:
            raise ValueError("입력 데이터가 비어 있습니다")

        for col in ("category", "value"):
            if col not in df.columns:
                raise ValueError(f"필수 컬럼이 누락되었습니다: {col}")

        if not pd.api.types.is_numeric_dtype(df["value"]):
            raise TypeError("'value' 컬럼은 숫자 타입이어야 합니다")

        threshold = parameters.get("threshold", self.DEFAULT_THRESHOLD)
        if not isinstance(threshold, (int, float)) or not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold는 0과 1 사이의 숫자여야 합니다")

        method = parameters.get("method", "mean")
        if method not in ("mean", "median", "max"):
            raise ValueError(f"지원하지 않는 방법입니다: {method}")

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        """메인 실행 로직. 반환 dict의 키는 출력 포트 label과 일치해야 한다."""
        self.validate(inputs, parameters)  # 잘못된 입력을 먼저 걸러낸다

        ctx.log_info("TemplateNode 실행 시작")

        df = inputs["input_data"].copy()  # 원본 보호를 위해 복사
        threshold = parameters.get("threshold", self.DEFAULT_THRESHOLD)
        method = parameters.get("method", "mean")

        ctx.progress(0.3)
        processed_df = self._process_data(df, threshold, method)

        ctx.progress(0.8)
        summary_df = self._summarize(df, processed_df)

        ctx.log_info(f"TemplateNode 실행 완료 (행 {len(df)} -> {len(processed_df)})")
        ctx.progress(1.0)

        return {
            "processed_data": processed_df,
            "summary": summary_df,
        }

    def _process_data(self, df: pd.DataFrame, threshold: float, method: str) -> pd.DataFrame:
        """임계값으로 필터링한 뒤 카테고리별로 집계한다."""
        filtered = df[df["value"] > threshold]
        aggregated = getattr(filtered.groupby("category")["value"], method)()
        return aggregated.reset_index()

    def _summarize(self, original: pd.DataFrame, processed: pd.DataFrame) -> pd.DataFrame:
        """화면 표시용 요약 테이블(DISPLAY 포트로 내보낸다)."""
        return pd.DataFrame(
            {
                "metric": ["original_rows", "processed_rows"],
                "value": [len(original), len(processed)],
            }
        )


# 파일 맨 끝에서 인스턴스를 하나 생성한다(SDK가 이 인스턴스를 찾는다).
node = TemplateNode()
```

## 데이터 처리 패턴

아래 헬퍼들은 SDK API가 아니라 평범한 pandas 유틸리티입니다. 노드의 `run()` 안에서 자유롭게 조합해 쓰면 됩니다.

### 1. 안전한 DataFrame 처리

```python
import logging

import pandas as pd

logger = logging.getLogger(__name__)


class SafeDataFrameProcessor:
    """안전한 DataFrame 처리 유틸리티 (평범한 헬퍼 — SDK API가 아님)."""

    @staticmethod
    def safe_copy(df: pd.DataFrame) -> pd.DataFrame:
        """메모리 사용량을 확인하며 복사한다."""
        if df.memory_usage(deep=True).sum() > 100_000_000:  # 100MB
            logger.warning("대용량 DataFrame 감지 — 청크 처리를 고려하세요")
        return df.copy()

    @staticmethod
    def safe_column_access(df: pd.DataFrame, column: str, default_value=None) -> pd.Series:
        """안전한 컬럼 접근."""
        if column not in df.columns:
            if default_value is not None:
                return pd.Series([default_value] * len(df), name=column)
            raise KeyError(f"컬럼 '{column}'을(를) 찾을 수 없습니다")
        return df[column]

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: str = "drop") -> pd.DataFrame:
        """결측값 처리."""
        if strategy == "drop":
            return df.dropna()
        if strategy == "fill_mean":
            return df.fillna(df.mean(numeric_only=True))
        if strategy == "fill_zero":
            return df.fillna(0)
        raise ValueError(f"알 수 없는 전략입니다: {strategy}")
```

헬퍼를 노드에서 사용하는 예:

```python
class DataProcessingNode(CustomNode):
    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="DataProcessing",
            category="custom",
            data=NodeData(
                input_ports=[
                    Port(type=PortEnum.TARGET, position=PositionEnum.LEFT,
                         port_type=PortTypeEnum.DATASET, label="input_data"),
                ],
                output_ports=[
                    Port(type=PortEnum.SOURCE, position=PositionEnum.RIGHT,
                         port_type=PortTypeEnum.DATASET, label="clean_data"),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = SafeDataFrameProcessor.safe_copy(inputs["input_data"])
        clean_df = SafeDataFrameProcessor.handle_missing_values(df, "fill_mean")
        ctx.log_info(f"결측값 처리 완료: {len(clean_df)}개 행")
        return {"clean_data": clean_df}


node = DataProcessingNode()
```

### 2. 메모리 효율적인 처리

타임아웃·취소는 플랫폼이 gRPC로 처리하므로 노드가 직접 관리할 필요는 없지만, 긴 루프에서는 `ctx.progress()`로 진행률을 알리는 것이 좋습니다.

```python
class MemoryEfficientNode(CustomNode):
    """청크 단위로 처리해 메모리를 절약하는 노드."""

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="MemoryEfficient",
            category="custom",
            data=NodeData(
                input_ports=[
                    Port(type=PortEnum.TARGET, position=PositionEnum.LEFT,
                         port_type=PortTypeEnum.DATASET, label="input_data"),
                ],
                output_ports=[
                    Port(type=PortEnum.SOURCE, position=PositionEnum.RIGHT,
                         port_type=PortTypeEnum.DATASET, label="output_data"),
                ],
                params=[
                    Parameter(text="청크 크기", name="chunk_size", form_type="number",
                              value=10000, value_type="number", is_tab=True),
                    Parameter(text="임계값", name="threshold", form_type="number",
                              value=0.0, value_type="number", is_tab=True),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs["input_data"]
        chunk_size = parameters.get("chunk_size", 10000)

        results = []
        total = max(len(df), 1)
        for start in range(0, len(df), chunk_size):
            chunk = df.iloc[start:start + chunk_size]
            results.append(self._process_chunk(chunk, parameters))
            ctx.progress(min((start + chunk_size) / total, 1.0))

        final_result = pd.concat(results, ignore_index=True)
        return {"output_data": final_result}

    def _process_chunk(self, chunk: pd.DataFrame, parameters: dict) -> pd.DataFrame:
        """청크별 처리 로직."""
        threshold = parameters.get("threshold", 0.0)
        return chunk[chunk["value"] > threshold]


node = MemoryEfficientNode()
```

### 3. 데이터 타입 변환

```python
import logging

import pandas as pd

logger = logging.getLogger(__name__)


class DataTypeConverter:
    """데이터 타입 변환 유틸리티 (평범한 헬퍼)."""

    @staticmethod
    def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame 데이터 타입 최적화."""
        optimized_df = df.copy()

        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype

            if col_type == "object":
                # 반복이 많은 문자열 컬럼을 category로 변환
                if optimized_df[col].nunique() / len(optimized_df) < 0.5:
                    optimized_df[col] = optimized_df[col].astype("category")

            elif col_type == "float64":
                # float32로 다운캐스팅 (정밀도 허용 범위 내에서)
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast="float")

            elif col_type == "int64":
                # 더 작은 정수 타입으로 다운캐스팅
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast="integer")

        return optimized_df

    @staticmethod
    def safe_numeric_conversion(series: pd.Series, errors: str = "coerce") -> pd.Series:
        """안전한 숫자 타입 변환."""
        return pd.to_numeric(series, errors=errors)

    @staticmethod
    def safe_datetime_conversion(series: pd.Series, fmt: str | None = None) -> pd.Series:
        """안전한 날짜 타입 변환."""
        try:
            return pd.to_datetime(series, format=fmt)
        except ValueError as exc:
            logger.warning(f"날짜 변환 실패, coerce로 재시도: {exc}")
            return pd.to_datetime(series, errors="coerce")
```

## 에러 처리 패턴

이 SDK의 예외 모델은 의도적으로 얇습니다.

- 공개 예외는 **`CustomNodeError`**(SDK 기본 예외)와 **`SecretNotAvailableError`**(둘 다 `from ai_canvas_sdk import ...`) 두 개뿐입니다. `NodeException`·`DataValidationError`·`ResourceError` 같은 클래스는 존재하지 않습니다.
- 잘못된 입력·파라미터는 **표준 예외**(`ValueError`/`TypeError`)로 던집니다. 보통 `validate()` 안에서 처리합니다.
- 그 밖의 예외(`KeyError`, `MemoryError` 등)는 **잡지 말고 그대로 전파**합니다. 플랫폼이 스택트레이스를 수집하고 실행을 실패로 표시합니다.
- `error_type`·`retryable`·`suggestions` 같은 인자는 없습니다. 예외는 그냥 메시지 문자열을 받습니다.
- 타입이 있는 도메인 예외가 꼭 필요하면 **`CustomNodeError`를 직접 상속**해 만들 수 있습니다.
- `ctx.get_secret(name)`은 시크릿이 없을 때 `SecretNotAvailableError`를 자동으로 던집니다.

### 1. 검증은 예외로, 나머지는 전파

```python
from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    NodeData,
    NodeSchema,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
)


class RobustNode(CustomNode):
    """입력을 검증하고, 실패를 명확한 예외로 알리는 노드."""

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="Robust",
            category="custom",
            data=NodeData(
                input_ports=[
                    Port(type=PortEnum.TARGET, position=PositionEnum.LEFT,
                         port_type=PortTypeEnum.DATASET, label="input_data"),
                ],
                output_ports=[
                    Port(type=PortEnum.SOURCE, position=PositionEnum.RIGHT,
                         port_type=PortTypeEnum.DATASET, label="output_data"),
                ],
            ),
        )

    def validate(self, inputs: dict, parameters: dict) -> None:
        df = inputs.get("input_data")
        if df is None or df.empty:
            raise ValueError("입력 데이터가 비어 있습니다")  # 사용자가 고칠 수 있는 오류
        if "value" not in df.columns:
            raise ValueError("필수 컬럼 'value'가 없습니다")
        if not isinstance(parameters.get("threshold", 0), (int, float)):
            raise TypeError("threshold는 숫자여야 합니다")

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        self.validate(inputs, parameters)  # 잘못된 입력은 여기서 걸러진다

        df = inputs["input_data"]
        # 예상치 못한 예외는 잡지 않고 그대로 전파한다.
        result = df[df["value"] > parameters.get("threshold", 0)]
        ctx.log_info(f"{len(result)}개 행 통과")
        return {"output_data": result}


node = RobustNode()
```

### 2. 타입이 있는 도메인 예외 (선택)

특정 실패를 구분해서 다루고 싶다면 `CustomNodeError`를 상속해 직접 정의합니다.

```python
from ai_canvas_sdk import CustomNode, CustomNodeError, NodeContext


class ResourceTooLargeError(CustomNodeError):
    """직접 정의한 도메인 예외 — 반드시 CustomNodeError를 상속한다."""


class ResourceAwareNode(CustomNode):
    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="ResourceAware",
            category="custom",
            data=NodeData(
                input_ports=[
                    Port(type=PortEnum.TARGET, position=PositionEnum.LEFT,
                         port_type=PortTypeEnum.DATASET, label="input_data"),
                ],
                output_ports=[
                    Port(type=PortEnum.SOURCE, position=PositionEnum.RIGHT,
                         port_type=PortTypeEnum.DATASET, label="output_data"),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs["input_data"]
        memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        if memory_mb > 1000:  # 1GB
            # 커스텀 예외를 쓰려면 CustomNodeError를 상속해 던진다.
            raise ResourceTooLargeError(f"데이터가 너무 큽니다: {memory_mb:.1f}MB")

        ctx.log_info(f"데이터 크기 {memory_mb:.1f}MB — 정상 처리")
        return {"output_data": df}


node = ResourceAwareNode()
```

### 3. 점진적 성능 저하 (Graceful Degradation)

데이터 크기에 따라 처리 전략을 바꾸되, 진행 상황은 `ctx.log_*`로 남깁니다.

```python
class AdaptiveNode(CustomNode):
    """데이터 크기에 따라 처리 전략을 바꾸는 노드."""

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="Adaptive",
            category="custom",
            data=NodeData(
                input_ports=[
                    Port(type=PortEnum.TARGET, position=PositionEnum.LEFT,
                         port_type=PortTypeEnum.DATASET, label="input_data"),
                ],
                output_ports=[
                    Port(type=PortEnum.SOURCE, position=PositionEnum.RIGHT,
                         port_type=PortTypeEnum.DATASET, label="output_data"),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs["input_data"]

        if len(df) < 1_000:
            ctx.log_info("정밀 처리 모드 (소량 데이터)")
            result = self._precise(df)
        elif len(df) < 100_000:
            ctx.log_info("균형 처리 모드 (중간 데이터)")
            result = self._balanced(df)
        else:
            ctx.log_warning("고속 처리 모드 — 샘플링으로 근사합니다 (대량 데이터)")
            result = self._fast(df)

        return {"output_data": result}

    def _precise(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby("category", as_index=False)["value"].mean()

    def _balanced(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby("category", as_index=False)["value"].mean()

    def _fast(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.sample(n=10_000).groupby("category", as_index=False)["value"].mean()


node = AdaptiveNode()
```

## 테스트 가능한 노드 설계

### 1. 의존성 주입 패턴

노드는 보통 상태를 갖지 않지만, 테스트를 쉽게 하려고 처리기를 주입받는 `__init__`을 두는 것은 괜찮습니다. `CustomNode`에는 커스텀 `__init__`이 없어 `super().__init__()` 호출은 무해합니다. 다만 기본값을 제공해 인자 없이도 `node = TestableNode()`로 생성되게 해야 합니다.

```python
from abc import ABC, abstractmethod

import pandas as pd

from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    NodeData,
    NodeSchema,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
)


class DataProcessor(ABC):
    """데이터 처리 인터페이스 (테스트 시 교체 가능)."""

    @abstractmethod
    def process(self, data: pd.DataFrame) -> pd.DataFrame: ...


class StandardDataProcessor(DataProcessor):
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        return data.groupby("category", as_index=False)["value"].mean()


class TestableNode(CustomNode):
    """처리기를 주입받아 테스트하기 쉬운 노드."""

    def __init__(self, data_processor: DataProcessor | None = None):
        super().__init__()  # CustomNode에는 커스텀 __init__이 없어 호출은 무해하다
        self.data_processor = data_processor or StandardDataProcessor()

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="Testable",
            category="custom",
            data=NodeData(
                input_ports=[
                    Port(type=PortEnum.TARGET, position=PositionEnum.LEFT,
                         port_type=PortTypeEnum.DATASET, label="input_data"),
                ],
                output_ports=[
                    Port(type=PortEnum.SOURCE, position=PositionEnum.RIGHT,
                         port_type=PortTypeEnum.DATASET, label="output_data"),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        processed = self.data_processor.process(inputs["input_data"])
        return {"output_data": processed}


# 테스트용 모의 처리기
class MockDataProcessor(DataProcessor):
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({"result": [1, 2, 3]})


def test_node():
    # NodeContext는 execution_id / node_id 가 필수 위치 인자다.
    ctx = NodeContext(execution_id="local-test", node_id="testable")
    node = TestableNode(data_processor=MockDataProcessor())
    sample = pd.DataFrame({"category": ["A"], "value": [1.0]})

    result = node.run({"input_data": sample}, {}, ctx)

    assert "output_data" in result


node = TestableNode()
```

### 2. 설정 가능한 노드

```python
from dataclasses import dataclass


@dataclass
class NodeConfig:
    """노드 설정 (평범한 dataclass)."""

    max_memory_mb: int = 1000
    chunk_size: int = 10000
    debug_mode: bool = False


class ConfigurableNode(CustomNode):
    """생성 시점 설정을 주입받는 노드.

    타임아웃/취소는 플랫폼이 gRPC로 처리하므로 노드가 직접 관리하지 않는다.
    노드는 필요할 때 ctx.is_cancelled()로 협조적 취소만 확인한다.
    """

    def __init__(self, config: NodeConfig | None = None):
        super().__init__()
        self.config = config or NodeConfig()

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="Configurable",
            category="custom",
            data=NodeData(
                input_ports=[
                    Port(type=PortEnum.TARGET, position=PositionEnum.LEFT,
                         port_type=PortTypeEnum.DATASET, label="input_data"),
                ],
                output_ports=[
                    Port(type=PortEnum.SOURCE, position=PositionEnum.RIGHT,
                         port_type=PortTypeEnum.DATASET, label="output_data"),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        if self.config.debug_mode:
            ctx.log_debug("디버그 모드 활성화")

        df = inputs["input_data"]
        results = []
        for start in range(0, len(df), self.config.chunk_size):
            if ctx.is_cancelled():  # 협조적 취소
                ctx.log_warning("실행이 취소되었습니다")
                break
            results.append(df.iloc[start:start + self.config.chunk_size])

        output = pd.concat(results, ignore_index=True) if results else df
        return {"output_data": output}


# 사용 예시
node = ConfigurableNode(config=NodeConfig(debug_mode=True, max_memory_mb=2000))
```

## 문서화 패턴

### 노드 문서화

`NodeSchema`에는 `description` 필드가 없습니다. 사람이 읽는 설명은 **클래스/메서드 docstring**과 **`NodeMetadata`**(`author`·`documentation_url` 등)에 담습니다.

```python
from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    NodeData,
    NodeMetadata,
    NodeSchema,
    Parameter,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
)


class DocumentedNode(CustomNode):
    """카테고리별 집계 노드.

    주요 기능:
    - 그룹별 집계
    - 통계 요약 생성 (count / mean / sum)

    사용 사례:
    - 고객 데이터 분석, 판매 데이터 요약, 성과 지표 계산

    NodeSchema에는 description 필드가 없으므로, 이런 설명은 docstring과
    NodeMetadata에 담는다.
    """

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="DocumentedNode",
            category="custom",
            version="1.2.0",
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="source_data",  # 필수 컬럼: category, value
                        required=True,
                    ),
                ],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="aggregated_result",
                    ),
                ],
                params=[
                    Parameter(
                        text="그룹화 컬럼",
                        name="group_by",
                        form_type="input",
                        value="category",
                        value_type="string",
                        is_tab=True,
                    ),
                ],
            ),
            metadata=NodeMetadata(
                author="Your Name",
                documentation_url="https://example.com/docs/documented-node",
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        """카테고리별로 value를 집계한다.

        Args:
            inputs: {"source_data": 처리할 DataFrame(필수 컬럼: category, value)}
            parameters: {"group_by": 그룹화 기준 컬럼명}
            ctx: 실행 컨텍스트(로깅/진행률/취소)

        Returns:
            {"aggregated_result": 그룹별 집계 DataFrame}

        Raises:
            ValueError: 그룹화 컬럼이 없는 경우
        """
        df = inputs["source_data"]
        group_by = parameters.get("group_by", "category")
        if group_by not in df.columns:
            raise ValueError(f"그룹화 컬럼 '{group_by}'이(가) 없습니다")

        result = df.groupby(group_by, as_index=False)["value"].agg(["count", "mean", "sum"])
        ctx.log_info(f"{len(result)}개 그룹으로 집계 완료")
        return {"aggregated_result": result}


node = DocumentedNode()
```

### 노드 문서 자동 추출

`get_schema`는 인스턴스 메서드이므로 **인스턴스에서 호출**합니다. `NodeSchema`에는 `description`·`inputs`·`outputs`·`parameters` 필드가 없으므로, 실제 필드(`name`, `version`, `data.input_ports`/`output_ports`/`params`)를 사용합니다.

```python
def extract_node_documentation(node: CustomNode) -> dict:
    """노드 인스턴스에서 문서 메타데이터를 자동 추출한다."""
    schema = node.get_schema()

    return {
        "name": schema.name,
        "version": schema.version,
        "category": schema.category,
        "input_ports": [p.label for p in schema.data.input_ports],
        "output_ports": [p.label for p in schema.data.output_ports],
        "parameters": [p.name for p in schema.data.params],
        "author": schema.metadata.author if schema.metadata else "",
        "class_doc": type(node).__doc__,
        "run_doc": node.run.__doc__,
    }


# 사용 예시
docs = extract_node_documentation(node)
print(docs["name"], docs["version"])
print("입력 포트:", docs["input_ports"])
print("출력 포트:", docs["output_ports"])
```

---

이러한 **체계적인 개발 패턴**을 따르면 **유지보수 가능하고, 테스트 가능하며, 확장 가능한** 커스텀 노드를 개발할 수 있습니다.
