"""DataFrame 포트는 행 수와 무관하게 Arrow IPC 로 직렬화한다.

AC-1628: JSON 경로(<1만 행)가 datetime/NaN 에서 깨지므로 DataFrame
인코드를 Arrow 로 통일한다. dict DISPLAY 포트의 Struct JSON 은 유지한다.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ai_canvas_sdk.grpc import custom_node_service_pb2 as pb
from ai_canvas_sdk.serialization import DataSerializer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def serializer() -> DataSerializer:
    return DataSerializer()


def _round_trip(serializer: DataSerializer, value, port_id="p"):
    port_data = serializer.serialize_value(value=value, port_id=port_id, port_name=port_id)
    return port_data, serializer.deserialize_value(pb.PortData.FromString(port_data.SerializeToString()))


class TestDataFrameAlwaysArrow:
    def test_small_frame_uses_arrow_not_json(self, serializer):
        df = pd.DataFrame({"a": [1, 2, 3]})
        port_data, out = _round_trip(serializer, df)
        assert port_data.metadata["format"] == "arrow"
        assert port_data.WhichOneof("data") == "binary_data"
        assert list(out["a"]) == [1, 2, 3]

    def test_no_row_count_json_branch(self):
        source = (ROOT / "ai_canvas_sdk" / "serialization.py").read_text(encoding="utf-8")
        assert "SMALL_DATA_THRESHOLD" not in source
        assert "_serialize_as_json" not in source

    def test_datetime_round_trip(self, serializer):
        df = pd.DataFrame(
            {
                "ts": pd.to_datetime(["2026-09-15 07:57:00", "2026-09-16 00:00:00"]),
                "label": ["a", "b"],
            }
        )
        port_data, out = _round_trip(serializer, df)
        assert port_data.metadata["format"] == "arrow"
        assert pd.api.types.is_datetime64_any_dtype(out["ts"])
        assert list(out["ts"]) == list(df["ts"])
        assert out["label"].tolist() == ["a", "b"]

    def test_unused_datetime_column_does_not_fail_whole_frame(self, serializer):
        df = pd.DataFrame(
            {
                "keep": ["x", "y"],
                "unused_ts": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            }
        )
        _, out = _round_trip(serializer, df)
        assert out["keep"].tolist() == ["x", "y"]
        assert list(out["unused_ts"]) == list(df["unused_ts"])

    def test_nan_and_inf_preserved(self, serializer):
        df = pd.DataFrame({"a": [1.0, float("nan"), float("inf"), float("-inf")]})
        _, out = _round_trip(serializer, df)
        assert bool(out["a"].isna().iloc[1])
        assert np.isinf(out["a"].iloc[2]) and out["a"].iloc[2] > 0
        assert np.isinf(out["a"].iloc[3]) and out["a"].iloc[3] < 0

    def test_date_decimal_bytes_round_trip(self, serializer):
        df = pd.DataFrame(
            {
                "d": [dt.date(2026, 9, 15)],
                "amt": [Decimal("1.25")],
                "b": [b"hello"],
            }
        )
        _, out = _round_trip(serializer, df)
        assert out["d"].iloc[0] == dt.date(2026, 9, 15)
        assert out["amt"].iloc[0] == Decimal("1.25")
        assert out["b"].iloc[0] == b"hello"

    def test_over_limit_raises(self, serializer, monkeypatch):
        monkeypatch.setattr(serializer, "GRPC_SIZE_LIMIT", 1)
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValueError, match="너무 큽니다"):
            serializer.serialize(df, "p", "p")


class TestDictJsonPathUnchanged:
    def test_dict_still_uses_json_struct(self, serializer):
        port_data = serializer.serialize_value(value={"rows": 10}, port_id="p", port_name="p")
        assert port_data.metadata["format"] == "json"
        assert port_data.WhichOneof("data") == "json_data"

    def test_dict_round_trip_stays_dict(self, serializer):
        port_data, out = _round_trip(serializer, {"rows": 10})
        assert port_data.metadata["format"] == "json"
        assert isinstance(out, dict)
        assert out == {"rows": 10}
        assert not isinstance(out, pd.DataFrame)
