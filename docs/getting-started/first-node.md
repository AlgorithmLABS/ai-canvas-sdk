# 첫 번째 노드 만들기

이 가이드에서는 실제 비즈니스 로직을 포함한 실용적인 커스텀 노드를 단계별로 개발합니다.

## 목표

**고객 데이터 분석 노드**를 만들어보겠습니다:
- 고객 구매 데이터 입력
- 구매 패턴 분석
- 고객 세그먼트 분류
- 시각화용 차트 데이터 출력

## 요구사항 분석

### 입력 데이터
- **customer_data**: 고객 정보 (DataFrame)
- **purchase_data**: 구매 내역 (DataFrame)

### 출력 데이터
- **customer_segments**: 세그먼트별 고객 목록 (DataFrame)
- **analytics_summary**: 분석 요약 통계 (dict)
- **chart_data**: 차트 렌더링용 데이터 (dict)

### 파라미터
- **segment_method**: 세그먼트 방법 (RFM, 구매액 기준)
- **min_purchase_amount**: 최소 구매 금액 기준

## Step 1: 노드 구조 설계

```python
# customer_analytics_node.py
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
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


class CustomerAnalyticsNode(CustomNode):
    """고객 데이터 분석 및 세그먼트 분류 노드"""

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="CustomerAnalytics",
            category="analytics",
            version="1.0.0",
            metadata=NodeMetadata(author="Your Company"),
            data=NodeData(
                # 입력 포트 정의
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="customer_data",
                    ),
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="purchase_data",
                    ),
                ],
                # 출력 포트 정의
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="customer_segments",
                    ),
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DISPLAY,
                        label="analytics_summary",
                    ),
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DISPLAY,
                        label="chart_data",
                    ),
                ],
                # 파라미터 정의
                params=[
                    Parameter(
                        text="세그먼트 방법",
                        name="segment_method",
                        form_type="select",
                        value="rfm",
                        options={
                            "items": [
                                {"label": "RFM 분석", "value": "rfm"},
                                {"label": "구매액 기준", "value": "purchase_amount"},
                                {"label": "구매 빈도", "value": "purchase_frequency"},
                            ]
                        },
                        is_tab=True,
                    ),
                    Parameter(
                        text="최소 구매 금액",
                        name="min_purchase_amount",
                        form_type="number",
                        value=10000,
                        value_type="number",
                        is_tab=True,
                    ),
                    Parameter(
                        text="분석 기간 (일)",
                        name="analysis_period_days",
                        form_type="number",
                        value=365,
                        value_type="number",
                        is_tab=True,
                    ),
                ],
            ),
        )
```

`get_schema`는 인스턴스 메서드이며(`self` 인자를 받습니다), 포트와 파라미터는 모두 `NodeSchema.data`(`NodeData`) 안에 정의합니다. `NodeSchema`에는 `display_name`/`description`/`author`/`inputs`/`outputs`/`parameters` 같은 필드가 없으니 주의하세요 — 작성자 정보는 `NodeMetadata`로, 포트/파라미터는 `NodeData`로 들어갑니다.

## Step 2: 입력 데이터 검증

```python
    def validate(self, inputs: dict[str, Any], parameters: dict[str, Any]) -> None:
        """입력 데이터 검증"""

        # DataFrame 존재 확인
        customer_df = inputs.get("customer_data")
        purchase_df = inputs.get("purchase_data")

        if customer_df is None or customer_df.empty:
            raise ValueError("고객 데이터가 비어있습니다")

        if purchase_df is None or purchase_df.empty:
            raise ValueError("구매 데이터가 비어있습니다")

        # 필수 컬럼 확인
        required_customer_cols = ["customer_id", "name", "email"]
        missing_cols = [col for col in required_customer_cols if col not in customer_df.columns]
        if missing_cols:
            raise ValueError(f"고객 데이터에 필수 컬럼이 없습니다: {missing_cols}")

        required_purchase_cols = ["customer_id", "purchase_date", "amount"]
        missing_cols = [col for col in required_purchase_cols if col not in purchase_df.columns]
        if missing_cols:
            raise ValueError(f"구매 데이터에 필수 컬럼이 없습니다: {missing_cols}")

        # 데이터 타입 확인
        if not pd.api.types.is_numeric_dtype(purchase_df["amount"]):
            raise ValueError("구매 금액(amount) 컬럼이 숫자 타입이 아닙니다")

        # 파라미터 검증
        min_amount = parameters.get("min_purchase_amount", 0)
        if min_amount < 0:
            raise ValueError("최소 구매 금액은 0 이상이어야 합니다")
```

`validate`는 `CustomNode`가 강제하는 메서드는 아니지만, 검증 실패 시 `ValueError`(또는 `TypeError`)를 raise하는 관례를 따릅니다. 별도의 커스텀 예외 클래스를 만들 필요는 없습니다.

## ⚙️ Step 3: 핵심 비즈니스 로직 구현

```python
    def run(self, inputs: dict[str, Any], parameters: dict[str, Any], ctx: NodeContext) -> dict[str, Any]:
        """메인 실행 로직"""

        ctx.log_info("고객 데이터 분석 시작")

        # 입력 데이터 준비
        customer_df = inputs["customer_data"].copy()
        purchase_df = inputs["purchase_data"].copy()

        segment_method = parameters.get("segment_method", "rfm")
        min_amount = parameters.get("min_purchase_amount", 10000)
        analysis_days = parameters.get("analysis_period_days", 365)

        # 데이터 전처리
        customer_df, purchase_df = self._preprocess_data(
            customer_df, purchase_df, min_amount, analysis_days
        )
        ctx.progress(0.3)

        # 고객별 집계 데이터 생성
        customer_metrics = self._calculate_customer_metrics(customer_df, purchase_df)
        ctx.progress(0.5)

        # 세그먼트 분류
        if segment_method == "rfm":
            customer_segments = self._rfm_segmentation(customer_metrics)
        elif segment_method == "purchase_amount":
            customer_segments = self._amount_segmentation(customer_metrics)
        else:  # purchase_frequency
            customer_segments = self._frequency_segmentation(customer_metrics)
        ctx.progress(0.7)

        # 분석 요약 생성
        analytics_summary = self._generate_analytics_summary(customer_segments)

        # 차트 데이터 생성
        chart_data = self._generate_chart_data(customer_segments)
        ctx.progress(1.0)

        ctx.log_info(f"고객 데이터 분석 완료: {len(customer_segments)}명 처리")

        return {
            "customer_segments": customer_segments,
            "analytics_summary": analytics_summary,
            "chart_data": chart_data,
        }

    def _preprocess_data(
        self, customer_df: pd.DataFrame, purchase_df: pd.DataFrame,
        min_amount: float, analysis_days: int,
    ) -> tuple:
        """데이터 전처리"""

        # 날짜 컬럼 변환
        purchase_df["purchase_date"] = pd.to_datetime(purchase_df["purchase_date"])

        # 분석 기간 필터링
        cutoff_date = datetime.now() - timedelta(days=analysis_days)
        purchase_df = purchase_df[purchase_df["purchase_date"] >= cutoff_date]

        # 최소 구매 금액 필터링
        purchase_df = purchase_df[purchase_df["amount"] >= min_amount]

        # 유효한 고객만 유지
        valid_customers = purchase_df["customer_id"].unique()
        customer_df = customer_df[customer_df["customer_id"].isin(valid_customers)]

        return customer_df, purchase_df

    def _calculate_customer_metrics(
        self, customer_df: pd.DataFrame, purchase_df: pd.DataFrame
    ) -> pd.DataFrame:
        """고객별 메트릭 계산"""

        # 구매 집계
        purchase_metrics = purchase_df.groupby("customer_id").agg({
            "amount": ["sum", "mean", "count"],
            "purchase_date": ["min", "max"],
        }).reset_index()

        # 컬럼명 정리
        purchase_metrics.columns = [
            "customer_id", "total_amount", "avg_amount", "purchase_count",
            "first_purchase", "last_purchase",
        ]

        # RFM 메트릭 계산
        reference_date = datetime.now()
        purchase_metrics["recency_days"] = (
            reference_date - purchase_metrics["last_purchase"]
        ).dt.days

        purchase_metrics["frequency"] = purchase_metrics["purchase_count"]
        purchase_metrics["monetary"] = purchase_metrics["total_amount"]

        # 고객 정보와 결합
        customer_metrics = customer_df.merge(purchase_metrics, on="customer_id")

        return customer_metrics

    def _rfm_segmentation(self, customer_metrics: pd.DataFrame) -> pd.DataFrame:
        """RFM 기반 세그먼트 분류"""

        df = customer_metrics.copy()

        # RFM 점수 계산 (5점 척도)
        df["r_score"] = pd.qcut(df["recency_days"].rank(method="first"), 5,
                               labels=[5, 4, 3, 2, 1])  # 최근 구매일수록 높은 점수
        df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), 5,
                               labels=[1, 2, 3, 4, 5])  # 구매 빈도가 높을수록 높은 점수
        df["m_score"] = pd.qcut(df["monetary"].rank(method="first"), 5,
                               labels=[1, 2, 3, 4, 5])  # 구매 금액이 높을수록 높은 점수

        # RFM 점수를 문자열로 결합
        df["rfm_score"] = df["r_score"].astype(str) + df["f_score"].astype(str) + df["m_score"].astype(str)

        # 세그먼트 분류
        def classify_rfm_segment(rfm_score: str) -> str:
            """RFM 점수 기반 세그먼트 분류"""
            r, f, m = int(rfm_score[0]), int(rfm_score[1]), int(rfm_score[2])

            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"  # 최고 고객
            elif r >= 3 and f >= 3 and m >= 3:
                return "Loyal Customers"  # 충성 고객
            elif r >= 4 and f <= 2:
                return "New Customers"  # 신규 고객
            elif r <= 2 and f >= 3:
                return "At Risk"  # 이탈 위험
            elif r <= 2 and f <= 2:
                return "Lost Customers"  # 이탈 고객
            else:
                return "Potential Loyalists"  # 잠재 충성 고객

        df["segment"] = df["rfm_score"].apply(classify_rfm_segment)

        return df

    def _amount_segmentation(self, customer_metrics: pd.DataFrame) -> pd.DataFrame:
        """구매액 기준 세그먼트 분류"""

        df = customer_metrics.copy()

        # 구매액 기준 분위수 계산
        df["amount_quantile"] = pd.qcut(df["total_amount"], 4,
                                       labels=["Low", "Medium", "High", "Premium"])
        df["segment"] = df["amount_quantile"].astype(str) + " Value"

        return df

    def _frequency_segmentation(self, customer_metrics: pd.DataFrame) -> pd.DataFrame:
        """구매 빈도 기준 세그먼트 분류"""

        df = customer_metrics.copy()

        # 구매 빈도 기준 분류
        conditions = [
            df["purchase_count"] >= 10,
            df["purchase_count"] >= 5,
            df["purchase_count"] >= 2,
            df["purchase_count"] >= 1,
        ]

        choices = ["Frequent Buyer", "Regular Buyer", "Occasional Buyer", "One-time Buyer"]
        df["segment"] = np.select(conditions, choices, default="No Purchase")

        return df

    def _generate_analytics_summary(self, customer_segments: pd.DataFrame) -> dict[str, Any]:
        """분석 요약 통계 생성"""

        total_customers = len(customer_segments)
        total_revenue = customer_segments["total_amount"].sum()
        avg_purchase = customer_segments["avg_amount"].mean()

        # 세그먼트별 통계
        segment_stats = customer_segments.groupby("segment").agg({
            "customer_id": "count",
            "total_amount": ["sum", "mean"],
            "purchase_count": "mean",
            "recency_days": "mean",
        }).round(2)

        segment_summary = {}
        for segment in segment_stats.index:
            segment_summary[segment] = {
                "customer_count": int(segment_stats.loc[segment, ("customer_id", "count")]),
                "total_revenue": float(segment_stats.loc[segment, ("total_amount", "sum")]),
                "avg_customer_value": float(segment_stats.loc[segment, ("total_amount", "mean")]),
                "avg_purchase_frequency": float(segment_stats.loc[segment, ("purchase_count", "mean")]),
                "avg_recency_days": float(segment_stats.loc[segment, ("recency_days", "mean")]),
            }

        return {
            "total_customers": total_customers,
            "total_revenue": float(total_revenue),
            "average_purchase_amount": float(avg_purchase),
            "analysis_timestamp": datetime.now().isoformat(),
            "segment_summary": segment_summary,
        }

    def _generate_chart_data(self, customer_segments: pd.DataFrame) -> dict[str, Any]:
        """시각화용 차트 데이터 생성"""

        # 세그먼트별 고객 수
        segment_counts = customer_segments["segment"].value_counts().to_dict()

        # 세그먼트별 매출
        segment_revenue = customer_segments.groupby("segment")["total_amount"].sum().to_dict()

        # 구매 금액 분포
        amount_bins = pd.cut(customer_segments["total_amount"], bins=10)
        amount_distribution = amount_bins.value_counts().sort_index()

        return {
            "segment_counts": {
                "labels": list(segment_counts.keys()),
                "data": list(segment_counts.values()),
                "chart_type": "pie",
            },
            "segment_revenue": {
                "labels": list(segment_revenue.keys()),
                "data": list(segment_revenue.values()),
                "chart_type": "bar",
            },
            "amount_distribution": {
                "labels": [str(interval) for interval in amount_distribution.index],
                "data": list(amount_distribution.values),
                "chart_type": "histogram",
            },
        }


# 노드 인스턴스 생성
node = CustomerAnalyticsNode()
```

`run`은 항상 `(self, inputs, parameters, ctx)` 4개 인자를 받고, 반환값은 **출력 포트의 `label`을 키로 하는 dict**여야 합니다. 여기서는 `customer_segments`/`analytics_summary`/`chart_data`가 `get_schema`에서 선언한 출력 포트 label과 정확히 일치합니다. `ctx.log_info`로 로그를 남기고 `ctx.progress(0.0~1.0)`로 진행률을 보고할 수 있습니다.

`analytics_summary`와 `chart_data`는 표 형태가 아닌 dict이므로 `PortTypeEnum.DISPLAY` 포트로 노출합니다 — `PortTypeEnum`에는 별도의 `JSON` 타입이 없습니다.

## Step 4: 테스트 데이터 생성

```python
# test_customer_analytics.py
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from ai_canvas_sdk import NodeContext
from customer_analytics_node import CustomerAnalyticsNode


def create_test_data():
    """테스트용 샘플 데이터 생성"""

    # 고객 데이터 생성
    np.random.seed(42)
    customer_data = pd.DataFrame({
        "customer_id": [f"CUST_{i:04d}" for i in range(1, 1001)],
        "name": [f"Customer {i}" for i in range(1, 1001)],
        "email": [f"customer{i}@example.com" for i in range(1, 1001)],
        "signup_date": [datetime.now() - timedelta(days=int(d)) for d in np.random.randint(30, 800, size=1000)],
    })

    # 구매 데이터 생성 (더 현실적인 분포)
    # 주의: 날짜는 오늘(datetime.now()) 기준 상대값으로 생성합니다.
    # 캘린더에 고정된 날짜(예: "2023-01-01")를 쓰면 노드의 analysis_period_days(최근 N일)
    # 필터에 걸려 시간이 지날수록 테스트 데이터가 전부 걸러지는 문제가 생깁니다.
    purchase_records = []

    for customer_id in customer_data["customer_id"]:
        # 고객별로 다른 구매 패턴
        num_purchases = np.random.poisson(5)  # 평균 5회 구매

        for _ in range(num_purchases):
            purchase_date = datetime.now() - timedelta(days=int(np.random.randint(1, 365)))
            amount = np.random.lognormal(mean=9, sigma=1)  # 로그 정규분포
            purchase_records.append({
                "customer_id": customer_id,
                "purchase_date": purchase_date,
                "amount": round(amount, 2),
                "product_id": f"PROD_{np.random.randint(1, 101):03d}",
            })

    purchase_data = pd.DataFrame(purchase_records)

    return customer_data, purchase_data


def test_node():
    """노드 테스트 실행"""

    # 테스트 데이터 생성
    customer_df, purchase_df = create_test_data()

    print("테스트 데이터:")
    print(f"   고객 수: {len(customer_df)}")
    print(f"   구매 기록 수: {len(purchase_df)}")

    # 노드 실행
    node = CustomerAnalyticsNode()

    # 다양한 파라미터로 테스트
    test_cases = [
        {
            "name": "RFM 분석",
            "params": {
                "segment_method": "rfm",
                "min_purchase_amount": 5000,
                "analysis_period_days": 365,
            },
        },
        {
            "name": "구매액 기준",
            "params": {
                "segment_method": "purchase_amount",
                "min_purchase_amount": 10000,
                "analysis_period_days": 180,
            },
        },
    ]

    for test_case in test_cases:
        print(f"\n테스트 케이스: {test_case['name']}")

        # execution_id/node_id는 필수 인자입니다 — NodeContext()는 TypeError로 즉시 깨집니다.
        ctx = NodeContext(execution_id="local-test", node_id="customer-analytics")
        result = node.run(
            inputs={
                "customer_data": customer_df,
                "purchase_data": purchase_df,
            },
            parameters=test_case["params"],
            ctx=ctx,
        )

        # 결과 출력
        summary = result["analytics_summary"]

        print(f"   총 고객 수: {summary['total_customers']}")
        print(f"   총 매출: {summary['total_revenue']:,.0f}원")
        print("   세그먼트별 고객 수:")

        for segment, stats in summary["segment_summary"].items():
            print(f"     {segment}: {stats['customer_count']}명")


if __name__ == "__main__":
    test_node()
```

## Step 5: 실행 및 테스트

```bash
# 스키마 검증
ai-canvas-sdk test customer_analytics_node.py --validate-only

# 테스트 데이터로 실행
python test_customer_analytics.py

# 입력과 파라미터를 지정한 실행
ai-canvas-sdk test customer_analytics_node.py \
  -i customer_data.json \
  -p '{"segment_method": "rfm"}' \
  -v
```

예상 출력:
```
테스트 데이터:
   고객 수: 1000
   구매 기록 수: 4,832

테스트 케이스: RFM 분석
   총 고객 수: 967
   총 매출: 48,234,567원
   세그먼트별 고객 수:
     Champions: 193명
     Loyal Customers: 241명
     New Customers: 89명
     Potential Loyalists: 267명
     At Risk: 134명
     Lost Customers: 43명
```

## Step 6: AI Canvas에서 시각화

차트 데이터를 활용하여 AI Canvas에서 시각화가 가능합니다. `chart_data`는 `DISPLAY` 포트를 통해 노출되는 dict이며(전용 JSON 포트 타입은 없습니다), AI Canvas는 이 dict을 받아 아래와 같은 형태로 렌더링합니다:

```json
{
  "chart_data": {
    "segment_counts": {
      "labels": ["Champions", "Loyal Customers", "At Risk"],
      "data": [193, 241, 134],
      "chart_type": "pie"
    },
    "segment_revenue": {
      "labels": ["Champions", "Loyal Customers", "At Risk"],
      "data": [15234567, 18234567, 3234567],
      "chart_type": "bar"
    }
  }
}
```

## 완료 체크리스트

- [x] **스키마 정의**: 입력/출력/파라미터 명확히 정의
- [x] **입력 검증**: validate() 메서드로 데이터 품질 보장
- [x] **비즈니스 로직**: 복잡한 분석 로직을 모듈화
- [x] **에러 처리**: 예외 상황에 대한 적절한 에러 메시지
- [x] **테스트 코드**: 다양한 시나리오 테스트
- [x] **성능 최적화**: 대용량 데이터 처리 고려
- [x] **문서화**: 파라미터와 출력에 대한 명확한 설명


---

**축하합니다!** 실용적인 비즈니스 로직을 포함한 첫 번째 커스텀 노드를 완성했습니다.
