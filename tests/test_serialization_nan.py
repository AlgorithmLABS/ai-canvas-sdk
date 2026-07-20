"""NaN/Inf 를 포함한 데이터의 JSON 경로 직렬화 회귀 테스트.

배경(2026-07-20 dev): NaN 이 든 DataFrame 이 JSON 경로(<1만 행)로 전달되면
수신 측 `_deserialize_from_json` 의 `MessageToDict` 가 protobuf 6.x 의
JSON 표준 준수 정책으로 ValueError("Fail to serialize NaN for
Value.number_value, which would parse as string_value") 를 던져 노드 실행이
전부 실패했다. 수정은 양방향:
- 인코드: NaN/Inf → None(JSON null) 정규화 (_sanitize_json_value)
- 디코드: MessageToDict 대신 Struct 직접 순회 (_proto_struct_to_python)
  → 구버전 sender 가 이미 NaN 을 담아 보낸 데이터도 읽을 수 있음
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from google.protobuf import any_pb2, struct_pb2

from ai_canvas_sdk.grpc import custom_node_service_pb2 as pb
from ai_canvas_sdk.serialization import DataSerializer, _proto_struct_to_python, _sanitize_json_value


@pytest.fixture
def serializer() -> DataSerializer:
    return DataSerializer()


def _round_trip(serializer: DataSerializer, value, port_id="p"):
    port_data = serializer.serialize_value(value=value, port_id=port_id, port_name=port_id)
    return serializer.deserialize_value(pb.PortData.FromString(port_data.SerializeToString()))


class TestNanDataFrameJsonPath:
    def test_nan_dataframe_round_trip(self, serializer):
        """dev 장애 재현 케이스: NaN 결측이 있는 소형 DataFrame (JSON 경로)."""
        df = pd.DataFrame({"a": [1.0, float("nan"), 3.0], "b": ["x", "y", "z"]})
        out = _round_trip(serializer, df)

        assert isinstance(out, pd.DataFrame)
        assert len(out) == 3
        # NaN → JSON null → pandas 가 float 컬럼에서 NaN 으로 복원
        assert out["a"].isna().tolist() == [False, True, False]
        assert out["a"].dropna().tolist() == [1.0, 3.0]

    def test_inf_dataframe_round_trip(self, serializer):
        df = pd.DataFrame({"a": [1.0, float("inf"), float("-inf")]})
        out = _round_trip(serializer, df)
        # Inf 도 JSON 비호환 → null 정규화 → NaN 복원
        assert out["a"].isna().tolist() == [False, True, True]

    def test_all_nan_column(self, serializer):
        df = pd.DataFrame({"a": [float("nan")] * 3, "b": [1, 2, 3]})
        out = _round_trip(serializer, df)
        assert out["a"].isna().all()
        assert out["b"].tolist() == [1, 2, 3]


class TestNanDictJsonPath:
    """dict 값의 인코드 새니타이즈 검증.

    주의: deserialize_value 는 metadata format=="json" 이면 dict 도 DataFrame
    경로로 라우팅하는 기존 동작(quirk, 이 수정 범위 밖)이 있어 round-trip 이
    아니라 직렬화된 Struct 내용을 직접 검사한다 — 목표는 "NaN 이 Struct 에
    들어가지 않는다"(protobuf json_format 거부 원천 차단)이다.
    """

    @staticmethod
    def _packed_struct(port_data: pb.PortData) -> dict:
        json_struct = struct_pb2.Struct()
        port_data.json_data.Unpack(json_struct)
        return _proto_struct_to_python(json_struct)

    def test_dict_with_nan_in_list_sanitized(self, serializer):
        """스크린샷 traceback 의 형태: 리스트(ListValue) 안의 NaN."""
        value = {"scores": [1.0, float("nan"), 3.0], "label": "ok"}
        port_data = serializer.serialize_value(value=value, port_id="p", port_name="p")
        stored = self._packed_struct(port_data)
        assert stored["scores"] == [1.0, None, 3.0]
        assert stored["label"] == "ok"

    def test_nested_dict_nan_sanitized(self, serializer):
        value = {"outer": {"inner": float("nan"), "keep": 2.5}}
        port_data = serializer.serialize_value(value=value, port_id="p", port_name="p")
        stored = self._packed_struct(port_data)
        assert stored["outer"]["inner"] is None
        assert stored["outer"]["keep"] == 2.5

    def test_json_data_without_format_decodes_nan_tolerantly(self, serializer):
        """metadata format 이 없는 외부 producer 의 json_data 분기 디코드 톨러런스."""
        json_struct = struct_pb2.Struct()
        json_struct.update({"v": float("nan")})
        json_any = any_pb2.Any()
        json_any.Pack(json_struct)
        port_data = pb.PortData(port_id="p", port_name="p", json_data=json_any)  # metadata 없음
        out = serializer.deserialize_value(port_data)
        assert math.isnan(out["v"])


class TestDecodeToleranceForLegacySenders:
    """구버전 sdk(sender)가 NaN 을 이미 Struct 에 담아 보낸 경우도 디코드 가능해야 한다."""

    def _legacy_dataframe_portdata(self) -> pb.PortData:
        # 구버전 _serialize_as_json 동작 모사: NaN 을 정규화 없이 Struct 에 저장
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
        return pb.PortData(
            port_id="p",
            port_name="p",
            port_type=pb.PORT_TYPE_DATASET,
            json_data=json_any,
            metadata={"format": "json"},
        )

    def test_legacy_nan_struct_decodes(self, serializer):
        out = serializer.deserialize_value(self._legacy_dataframe_portdata())
        assert isinstance(out, pd.DataFrame)
        assert out["a"].isna().tolist() == [False, True]

    def test_proto_struct_to_python_preserves_nan(self):
        s = struct_pb2.Struct()
        s.update({"v": float("nan"), "arr": [float("inf"), 1.0]})
        out = _proto_struct_to_python(s)
        assert math.isnan(out["v"])
        assert math.isinf(out["arr"][0]) and out["arr"][1] == 1.0


class TestSanitizeHelper:
    def test_sanitize_scalars_and_containers(self):
        assert _sanitize_json_value(float("nan")) is None
        assert _sanitize_json_value(float("inf")) is None
        assert _sanitize_json_value(1.5) == 1.5
        assert _sanitize_json_value({"a": [float("nan"), {"b": float("-inf")}]}) == {"a": [None, {"b": None}]}
        assert _sanitize_json_value("NaN") == "NaN"  # 문자열은 건드리지 않음

    def test_numpy_nan_handled(self):
        # numpy float 도 float 서브클래스라 동일 처리
        assert _sanitize_json_value(float(np.float64("nan"))) is None


class TestArrowPathUnaffected:
    def test_arrow_path_preserves_nan(self, serializer):
        """중간 크기(Arrow 경로)는 원래도 NaN 을 보존한다 — 회귀 없음 확인."""
        rows = 20_000
        df = pd.DataFrame({"a": np.arange(rows, dtype=np.float64)})
        df.loc[1, "a"] = np.nan
        out = _round_trip(serializer, df)
        assert bool(out["a"].isna().iloc[1])
        assert len(out) == rows
