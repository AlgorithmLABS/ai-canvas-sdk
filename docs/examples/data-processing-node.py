"""
데이터 처리 노드 예제

고객 데이터를 처리하여 다양한 분석 결과를 제공하는 커스텀 노드 예제입니다.
기본적인 데이터 정제, 집계, 통계 생성 기능을 포함합니다.
"""

import logging
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

logger = logging.getLogger(__name__)


class CustomerDataProcessor(CustomNode):
    """고객 데이터 처리 노드

    고객 기본 정보와 구매 이력을 분석하여 고객 세그먼트와 통계를 생성합니다.
    """

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="CustomerDataProcessor",
            category="data_processing",
            version="1.0.0",
            metadata=NodeMetadata(author="AI Canvas Team"),
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="customer_info",
                    ),
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="purchase_history",
                    ),
                ],
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
                        port_type=PortTypeEnum.DATASET,
                        label="purchase_analytics",
                    ),
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DISPLAY,
                        label="summary_statistics",
                    ),
                ],
                params=[
                    Parameter(
                        text="분석 기간 (일)",
                        name="analysis_period_days",
                        form_type="number",
                        value=365,
                    ),
                    Parameter(
                        text="최소 구매 금액",
                        name="min_purchase_amount",
                        form_type="number",
                        value=0,
                    ),
                    Parameter(
                        text="세그먼트 방법",
                        name="segment_method",
                        form_type="select",
                        value="rfm",
                        options={
                            "items": [
                                {"label": "RFM 분석", "value": "rfm"},
                                {"label": "구매액 기준", "value": "monetary"},
                                {"label": "구매 빈도 기준", "value": "frequency"},
                            ]
                        },
                    ),
                ],
            ),
        )

    def validate(self, inputs: dict[str, Any], parameters: dict[str, Any]) -> None:
        """입력 데이터 검증"""

        # 고객 정보 검증
        customer_df = inputs.get("customer_info")
        if customer_df is None or customer_df.empty:
            raise ValueError("고객 정보가 비어있습니다")

        required_customer_cols = ["customer_id", "name", "email", "signup_date"]
        missing_cols = [col for col in required_customer_cols if col not in customer_df.columns]
        if missing_cols:
            raise ValueError(f"고객 정보에 필수 컬럼이 누락되었습니다: {missing_cols}")

        # 구매 이력 검증
        purchase_df = inputs.get("purchase_history")
        if purchase_df is None or purchase_df.empty:
            raise ValueError("구매 이력이 비어있습니다")

        required_purchase_cols = ["customer_id", "purchase_date", "amount"]
        missing_cols = [col for col in required_purchase_cols if col not in purchase_df.columns]
        if missing_cols:
            raise ValueError(f"구매 이력에 필수 컬럼이 누락되었습니다: {missing_cols}")

        # 데이터 타입 검증
        if not pd.api.types.is_numeric_dtype(purchase_df["amount"]):
            raise ValueError("구매 금액(amount)은 숫자 타입이어야 합니다")

        # 고객 ID 일치 확인
        customer_ids = set(customer_df["customer_id"])
        purchase_customer_ids = set(purchase_df["customer_id"])
        if not purchase_customer_ids.issubset(customer_ids):
            missing_customers = purchase_customer_ids - customer_ids
            logger.warning(f"구매 이력에 있지만 고객 정보에 없는 ID: {len(missing_customers)}개")

    def run(self, inputs: dict[str, Any], parameters: dict[str, Any], ctx: NodeContext) -> dict[str, Any]:
        """메인 실행 로직"""

        logger.info("고객 데이터 처리 시작")

        # 입력 데이터 준비
        customer_df = inputs["customer_info"].copy()
        purchase_df = inputs["purchase_history"].copy()

        # 파라미터
        analysis_days = parameters.get("analysis_period_days", 365)
        min_amount = parameters.get("min_purchase_amount", 0)
        segment_method = parameters.get("segment_method", "rfm")

        # 1. 데이터 전처리
        customer_df, purchase_df = self._preprocess_data(customer_df, purchase_df, analysis_days, min_amount)

        # 2. 구매 분석
        purchase_analytics = self._analyze_purchase_patterns(customer_df, purchase_df)

        # 3. 고객 세그먼테이션
        customer_segments = self._segment_customers(purchase_analytics, segment_method)

        # 4. 요약 통계 생성
        summary_stats = self._generate_summary_statistics(customer_df, purchase_df, customer_segments)

        logger.info("고객 데이터 처리 완료")

        return {
            "customer_segments": customer_segments,
            "purchase_analytics": purchase_analytics,
            "summary_statistics": summary_stats,
        }

    def _preprocess_data(
        self, customer_df: pd.DataFrame, purchase_df: pd.DataFrame, analysis_days: int, min_amount: float
    ) -> tuple:
        """데이터 전처리"""

        # 날짜 컬럼 변환
        purchase_df["purchase_date"] = pd.to_datetime(purchase_df["purchase_date"])
        customer_df["signup_date"] = pd.to_datetime(customer_df["signup_date"])

        # 분석 기간 필터링
        cutoff_date = datetime.now() - timedelta(days=analysis_days)
        purchase_df = purchase_df[purchase_df["purchase_date"] >= cutoff_date]

        # 최소 구매 금액 필터링
        purchase_df = purchase_df[purchase_df["amount"] >= min_amount]

        # 유효한 고객만 유지
        valid_customers = purchase_df["customer_id"].unique()
        customer_df = customer_df[customer_df["customer_id"].isin(valid_customers)]

        logger.info(f"전처리 후 고객 수: {len(customer_df)}, 구매 기록: {len(purchase_df)}")

        return customer_df, purchase_df

    def _analyze_purchase_patterns(self, customer_df: pd.DataFrame, purchase_df: pd.DataFrame) -> pd.DataFrame:
        """구매 패턴 분석"""

        # 고객별 구매 집계
        purchase_metrics = (
            purchase_df.groupby("customer_id")
            .agg(
                {
                    "amount": ["sum", "mean", "count", "std"],
                    "purchase_date": ["min", "max", "nunique"],
                    "product_category": lambda x: x.nunique() if "product_category" in purchase_df.columns else 0,
                }
            )
            .round(2)
        )

        # 컬럼명 정리
        purchase_metrics.columns = [
            "total_amount",
            "avg_amount",
            "purchase_count",
            "amount_std",
            "first_purchase",
            "last_purchase",
            "purchase_days",
            "category_diversity",
        ]

        purchase_metrics = purchase_metrics.reset_index()

        # RFM 메트릭 계산
        reference_date = datetime.now()
        purchase_metrics["recency_days"] = (reference_date - purchase_metrics["last_purchase"]).dt.days

        purchase_metrics["frequency"] = purchase_metrics["purchase_count"]
        purchase_metrics["monetary"] = purchase_metrics["total_amount"]

        # 고객 정보와 결합
        analytics = customer_df.merge(purchase_metrics, on="customer_id", how="inner")

        # 추가 메트릭 계산
        analytics["avg_days_between_purchase"] = (
            (analytics["last_purchase"] - analytics["first_purchase"]).dt.days / (analytics["purchase_count"] - 1)
        ).fillna(0)

        analytics["customer_lifetime_days"] = (reference_date - analytics["signup_date"]).dt.days

        analytics["purchase_rate"] = (analytics["purchase_count"] / analytics["customer_lifetime_days"] * 30).round(
            3
        )  # 월 평균 구매 횟수

        return analytics

    def _segment_customers(self, analytics_df: pd.DataFrame, method: str) -> pd.DataFrame:
        """고객 세그먼테이션"""

        df = analytics_df.copy()

        if method == "rfm":
            return self._rfm_segmentation(df)
        elif method == "monetary":
            return self._monetary_segmentation(df)
        elif method == "frequency":
            return self._frequency_segmentation(df)
        else:
            raise ValueError(f"지원하지 않는 세그먼트 방법: {method}")

    def _rfm_segmentation(self, df: pd.DataFrame) -> pd.DataFrame:
        """RFM 분석 기반 세그먼테이션"""

        # RFM 점수 계산 (1-5점 척도)
        df["r_score"] = pd.qcut(
            df["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]
        )  # 최근일수록 높은 점수
        df["f_score"] = pd.qcut(
            df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
        )  # 빈도가 높을수록 높은 점수
        df["m_score"] = pd.qcut(
            df["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
        )  # 금액이 높을수록 높은 점수

        # RFM 점수 문자열 생성
        df["rfm_score"] = df["r_score"].astype(str) + df["f_score"].astype(str) + df["m_score"].astype(str)

        # 세그먼트 분류
        def classify_rfm_segment(rfm_score: str) -> str:
            r, f, m = int(rfm_score[0]), int(rfm_score[1]), int(rfm_score[2])

            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"  # 최고 고객
            elif r >= 4 and f >= 3 and m >= 3:
                return "Loyal Customers"  # 충성 고객
            elif r >= 4 and f <= 2 and m >= 3:
                return "Potential Loyalists"  # 잠재 충성 고객
            elif r >= 4 and f <= 2 and m <= 2:
                return "New Customers"  # 신규 고객
            elif r >= 3 and f >= 3 and m >= 3:
                return "Need Attention"  # 관심 필요
            elif r <= 2 and f >= 3 and m >= 3:
                return "At Risk"  # 이탈 위험
            elif r <= 2 and f <= 2 and m >= 3:
                return "Cannot Lose Them"  # 잃어선 안될 고객
            elif r <= 2 and f <= 2 and m <= 2:
                return "Lost"  # 이탈 고객
            else:
                return "Others"

        df["segment"] = df["rfm_score"].apply(classify_rfm_segment)
        df["segmentation_method"] = "RFM"

        return df

    def _monetary_segmentation(self, df: pd.DataFrame) -> pd.DataFrame:
        """구매액 기준 세그먼테이션"""

        # 구매액 기준 분위수 계산
        df["monetary_quartile"] = pd.qcut(df["monetary"], 4, labels=["Bronze", "Silver", "Gold", "Platinum"])
        df["segment"] = df["monetary_quartile"].astype(str) + " Customer"
        df["segmentation_method"] = "Monetary"

        return df

    def _frequency_segmentation(self, df: pd.DataFrame) -> pd.DataFrame:
        """구매 빈도 기준 세그먼테이션"""

        # 구매 빈도 기준 분류
        conditions = [df["frequency"] >= 10, df["frequency"] >= 5, df["frequency"] >= 2, df["frequency"] >= 1]

        choices = ["Power User", "Regular User", "Occasional User", "One-time User"]
        df["segment"] = np.select(conditions, choices, default="Inactive")
        df["segmentation_method"] = "Frequency"

        return df

    def _generate_summary_statistics(
        self, customer_df: pd.DataFrame, purchase_df: pd.DataFrame, segments_df: pd.DataFrame
    ) -> dict[str, Any]:
        """요약 통계 생성"""

        total_customers = len(customer_df)
        total_purchases = len(purchase_df)
        total_revenue = purchase_df["amount"].sum()
        avg_order_value = purchase_df["amount"].mean()

        # 세그먼트별 통계
        segment_stats = (
            segments_df.groupby("segment")
            .agg(
                {
                    "customer_id": "count",
                    "total_amount": ["sum", "mean"],
                    "purchase_count": "mean",
                    "recency_days": "mean",
                    "avg_amount": "mean",
                }
            )
            .round(2)
        )

        segment_summary = {}
        for segment in segment_stats.index:
            segment_summary[segment] = {
                "customer_count": int(segment_stats.loc[segment, ("customer_id", "count")]),
                "total_revenue": float(segment_stats.loc[segment, ("total_amount", "sum")]),
                "avg_customer_value": float(segment_stats.loc[segment, ("total_amount", "mean")]),
                "avg_purchase_frequency": float(segment_stats.loc[segment, ("purchase_count", "mean")]),
                "avg_recency_days": float(segment_stats.loc[segment, ("recency_days", "mean")]),
                "avg_order_value": float(segment_stats.loc[segment, ("avg_amount", "mean")]),
            }

        # 시간별 트렌드
        if "purchase_date" in purchase_df.columns:
            monthly_trend = purchase_df.groupby(purchase_df["purchase_date"].dt.to_period("M")).agg(
                {"amount": ["sum", "count"], "customer_id": "nunique"}
            )

            trend_data = []
            for period, data in monthly_trend.iterrows():
                trend_data.append(
                    {
                        "period": str(period),
                        "revenue": float(data[("amount", "sum")]),
                        "orders": int(data[("amount", "count")]),
                        "customers": int(data[("customer_id", "nunique")]),
                    }
                )
        else:
            trend_data = []

        return {
            "overview": {
                "total_customers": total_customers,
                "total_purchases": total_purchases,
                "total_revenue": float(total_revenue),
                "average_order_value": float(avg_order_value),
                "revenue_per_customer": float(total_revenue / total_customers) if total_customers > 0 else 0,
            },
            "segment_breakdown": segment_summary,
            "monthly_trends": trend_data,
            "data_quality": {
                "customer_data_completeness": float(
                    (customer_df.notna().sum().sum()) / (len(customer_df) * len(customer_df.columns))
                ),
                "purchase_data_completeness": float(
                    (purchase_df.notna().sum().sum()) / (len(purchase_df) * len(purchase_df.columns))
                ),
            },
            "analysis_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "segmentation_method": segments_df["segmentation_method"].iloc[0],
                "total_segments": len(segment_summary),
            },
        }

    def cleanup(self) -> None:
        """리소스 정리"""
        logger.info("CustomerDataProcessor 정리 완료")


# 노드 인스턴스 생성
node = CustomerDataProcessor()


# 테스트 데이터 생성 함수 (개발/테스트용)
def create_sample_data():
    """샘플 데이터 생성"""
    import random
    from datetime import datetime, timedelta

    # 고객 정보 생성
    customers = []
    for i in range(1, 1001):
        customers.append(
            {
                "customer_id": f"CUST_{i:04d}",
                "name": f"Customer {i}",
                "email": f"customer{i}@example.com",
                "signup_date": datetime.now() - timedelta(days=random.randint(30, 800)),
                "age_group": random.choice(["20s", "30s", "40s", "50s", "60+"]),
            }
        )

    customer_df = pd.DataFrame(customers)

    # 구매 이력 생성
    purchases = []
    categories = ["Electronics", "Clothing", "Books", "Food", "Sports", "Beauty"]

    for customer_id in customer_df["customer_id"]:
        # 고객별로 다른 구매 패턴
        num_purchases = np.random.poisson(5)  # 평균 5회 구매

        if num_purchases > 0:
            for _ in range(num_purchases):
                purchase_date = datetime.now() - timedelta(days=random.randint(1, 365))
                amount = max(10, np.random.lognormal(4, 1))  # 로그 정규분포

                purchases.append(
                    {
                        "customer_id": customer_id,
                        "purchase_date": purchase_date,
                        "amount": round(amount, 2),
                        "product_category": random.choice(categories),
                    }
                )

    purchase_df = pd.DataFrame(purchases)

    return customer_df, purchase_df


# 사용 예시
if __name__ == "__main__":
    # 샘플 데이터 생성
    customer_data, purchase_data = create_sample_data()

    print(f"생성된 고객 수: {len(customer_data)}")
    print(f"생성된 구매 기록: {len(purchase_data)}")

    # 노드 실행 테스트
    inputs = {"customer_info": customer_data, "purchase_history": purchase_data}

    parameters = {"analysis_period_days": 365, "min_purchase_amount": 10, "segment_method": "rfm"}

    try:
        ctx = NodeContext()
        result = node.run(inputs, parameters, ctx)

        print("노드 실행 성공!")
        print(f"고객 세그먼트: {result['customer_segments']['segment'].value_counts()}")
        print(f"총 매출: {result['summary_statistics']['overview']['total_revenue']:,.0f}원")

    except Exception as e:
        print(f"노드 실행 실패: {str(e)}")
