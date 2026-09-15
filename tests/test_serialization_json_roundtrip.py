"""JSON 경로(<1만 행) DataSerializer 왕복 회귀.

AC-1628: datetime 등 protobuf Struct 비호환 타입이 인코드에서
ValueError('Unexpected type') 를 내고, NaN 은 인코드는 통과하지만
protobuf 6.x MessageToDict 가 디코드에서 거절한다. 인코더·디코더가
같은 JSON 안전 타입 계약을 갖도록 고정한다.
"""

from __future__ import annotations

import datetime as dt
import math
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from google.protobuf import any_pb2, struct_pb2

from ai_canvas_sdk.grpc import custom_node_service_pb2 as pb
from ai_canvas_sdk.serialization import (
    DataSerializer,
    _proto_struct_to_python,
    _sanitize_json_value,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def serializer() -> DataSerializer:
    return DataSerializer()


def _round_trip(serializer: DataSerializer, value, port_id="p"):
    port_data = serializer.serialize_value(value=value, port_id=port_id, port_name=port_id)
    return serializer.deserialize_value(pb.PortData.FromString(port_data.SerializeToString()))


def _packed_struct(port_data: pb.PortData) -> dict:
    json_struct = struct_pb2.Struct()
    port_data.json_data.Unpack(json_struct)
    return _proto_struct_to_python(json_struct)


class TestIssueTableJsonEncode:
    """이슈에 적힌 컬럼 타입 표 — JSON 인코드가 예외 없이 끝나야 한다."""

    def test_datetime64_encodes(self, serializer):
        df = pd.DataFrame({"ts": pd.to_datetime(["2026-09-15 07:57:00"])})
        port_data = serializer.serialize(df, "p", "p")
        assert port_data.metadata["format"] == "json"
        stored = _packed_struct(port_data)
        assert stored["data"][0]["ts"] == "2026-09-15T07:57:00"

    def test_date_encodes(self, serializer):
        df = pd.DataFrame({"d": [dt.date(2026, 9, 15)]})
        stored = _packed_struct(serializer.serialize(df, "p", "p"))
        assert stored["data"][0]["d"] == "2026-09-15"

    def test_timedelta_encodes(self, serializer):
        df = pd.DataFrame({"td": [pd.Timedelta(seconds=90)]})
        stored = _packed_struct(serializer.serialize(df, "p", "p"))
        assert stored["data"][0]["td"] == 90.0

    def test_decimal_encodes(self, serializer):
        df = pd.DataFrame({"amt": [Decimal("1.25")]})
        stored = _packed_struct(serializer.serialize(df, "p", "p"))
        assert stored["data"][0]["amt"] == "1.25"

    def test_bytes_encodes(self, serializer):
        df = pd.DataFrame({"b": [b"hello"]})
        stored = _packed_struct(serializer.serialize(df, "p", "p"))
        assert stored["data"][0]["b"] == "hello"

    def test_bytes_non_utf8_encodes_base64(self, serializer):
        df = pd.DataFrame({"b": [b"\xff\xfe"]})
        stored = _packed_struct(serializer.serialize(df, "p", "p"))
        assert stored["data"][0]["b"] == "//4="

    def test_plain_types_still_encode(self, serializer):
        df = pd.DataFrame(
            {
                "s": ["x"],
                "i": np.int64(1),
                "f": np.float64(1.5),
                "flag": [True],
                "cat": pd.Series(["a"], dtype="category"),
                "none": [None],
                "nested": [[1, 2]],
            }
        )
        stored = _packed_struct(serializer.serialize(df, "p", "p"))
        row = stored["data"][0]
        assert row["s"] == "x"
        assert row["i"] == 1
        assert row["f"] == 1.5
        assert row["flag"] is True
        assert row["cat"] == "a"
        assert row["none"] is None
        assert row["nested"] == [1, 2]


class TestJsonRoundTrip:
    def test_datetime_round_trip(self, serializer):
        df = pd.DataFrame(
            {
                "ts": pd.to_datetime(["2026-09-15 07:57:00", "2026-09-16 00:00:00"]),
                "label": ["a", "b"],
            }
        )
        out = _round_trip(serializer, df)
        assert list(pd.to_datetime(out["ts"])) == list(df["ts"])
        assert out["label"].tolist() == ["a", "b"]

    def test_timedelta_round_trip(self, serializer):
        df = pd.DataFrame({"td": pd.to_timedelta(["90s", "0s"])})
        out = _round_trip(serializer, df)
        restored = pd.to_timedelta(out["td"], unit="s")
        assert list(restored) == list(df["td"])

    def test_unused_datetime_column_does_not_fail_whole_frame(self, serializer):
        """노드가 쓰지 않는 datetime 컬럼이 있어도 DataFrame 전체가 실패하면 안 된다."""
        df = pd.DataFrame(
            {
                "keep": ["x", "y"],
                "unused_ts": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            }
        )
        out = _round_trip(serializer, df)
        assert out["keep"].tolist() == ["x", "y"]
        assert list(pd.to_datetime(out["unused_ts"])) == list(df["unused_ts"])

    def test_nan_dataframe_round_trip(self, serializer):
        df = pd.DataFrame({"a": [1.0, float("nan"), 3.0], "b": ["x", "y", "z"]})
        out = _round_trip(serializer, df)
        assert out["a"].isna().tolist() == [False, True, False]
        assert out["a"].dropna().tolist() == [1.0, 3.0]

    def test_inf_dataframe_round_trip(self, serializer):
        df = pd.DataFrame({"a": [1.0, float("inf"), float("-inf")]})
        out = _round_trip(serializer, df)
        assert out["a"].isna().tolist() == [False, True, True]

    def test_all_nan_column(self, serializer):
        df = pd.DataFrame({"a": [float("nan")] * 3, "b": [1, 2, 3]})
        out = _round_trip(serializer, df)
        assert out["a"].isna().all()
        assert out["b"].tolist() == [1, 2, 3]


class TestNanDictJsonPath:
    def test_dict_with_nan_in_list_sanitized(self, serializer):
        value = {"scores": [1.0, float("nan"), 3.0], "label": "ok"}
        stored = _packed_struct(serializer.serialize_value(value=value, port_id="p", port_name="p"))
        assert stored["scores"] == [1.0, None, 3.0]
        assert stored["label"] == "ok"

    def test_nested_dict_nan_sanitized(self, serializer):
        value = {"outer": {"inner": float("nan"), "keep": 2.5}}
        stored = _packed_struct(serializer.serialize_value(value=value, port_id="p", port_name="p"))
        assert stored["outer"]["inner"] is None
        assert stored["outer"]["keep"] == 2.5

    def test_json_data_without_format_decodes_nan_tolerantly(self, serializer):
        json_struct = struct_pb2.Struct()
        json_struct.update({"v": float("nan")})
        json_any = any_pb2.Any()
        json_any.Pack(json_struct)
        port_data = pb.PortData(port_id="p", port_name="p", json_data=json_any)
        out = serializer.deserialize_value(port_data)
        assert math.isnan(out["v"])


class TestDecodeToleranceForLegacySenders:
    def test_legacy_nan_struct_decodes(self, serializer):
        json_struct = struct_pb2.Struct()
        json_struct.update(
            {
                "data": [{"a": 1.0}, {"a": float("nan")}],
                "columns": ["a"],
                "dtypes": {"a": "float64"},
            }
        )
        json_any = any_pb2.Any()
        json_any.Pack(json_struct)
        port_data = pb.PortData(
            port_id="p",
            port_name="p",
            port_type=pb.PORT_TYPE_DATASET,
            json_data=json_any,
            metadata={"format": "json"},
        )
        out = serializer.deserialize_value(port_data)
        assert out["a"].isna().tolist() == [False, True]

    def test_proto_struct_to_python_preserves_nan(self):
        s = struct_pb2.Struct()
        s.update({"v": float("nan"), "arr": [float("inf"), 1.0]})
        out = _proto_struct_to_python(s)
        assert math.isnan(out["v"])
        assert math.isinf(out["arr"][0]) and out["arr"][1] == 1.0


class TestSanitizeHelper:
    def test_sanitize_scalars_and_containers(self):
        ts = dt.datetime(2026, 9, 15, 7, 57)
        assert _sanitize_json_value(float("nan")) is None
        assert _sanitize_json_value(float("inf")) is None
        assert _sanitize_json_value(1.5) == 1.5
        assert _sanitize_json_value("NaN") == "NaN"
        assert _sanitize_json_value(ts) == "2026-09-15T07:57:00"
        assert _sanitize_json_value(dt.date(2026, 9, 15)) == "2026-09-15"
        assert _sanitize_json_value(dt.timedelta(seconds=90)) == 90.0
        assert _sanitize_json_value(Decimal("1.25")) == "1.25"
        assert _sanitize_json_value(b"hello") == "hello"
        assert _sanitize_json_value(np.int64(3)) == 3
        assert _sanitize_json_value({"a": [float("nan"), {"b": ts}]}) == {
            "a": [None, {"b": "2026-09-15T07:57:00"}]
        }

    def test_numpy_nan_handled(self):
        assert _sanitize_json_value(float(np.float64("nan"))) is None


class TestArrowPathUnaffected:
    def test_arrow_path_preserves_nan(self, serializer):
        rows = 20_000
        df = pd.DataFrame({"a": np.arange(rows, dtype=np.float64)})
        df.loc[1, "a"] = np.nan
        out = _round_trip(serializer, df)
        assert bool(out["a"].isna().iloc[1])
        assert len(out) == rows

    def test_arrow_path_preserves_datetime(self, serializer):
        rows = 20_000
        df = pd.DataFrame({"ts": pd.date_range("2026-01-01", periods=rows, freq="s")})
        out = _round_trip(serializer, df)
        assert len(out) == rows
        assert pd.api.types.is_datetime64_any_dtype(out["ts"])
        assert out["ts"].iloc[0] == df["ts"].iloc[0]


class TestNoMessageToDict:
    def test_serialization_module_does_not_import_message_to_dict(self):
        source = (ROOT / "ai_canvas_sdk" / "serialization.py").read_text(encoding="utf-8")
        assert "from google.protobuf.json_format import MessageToDict" not in source
        assert "json_format.MessageToDict(" not in source
