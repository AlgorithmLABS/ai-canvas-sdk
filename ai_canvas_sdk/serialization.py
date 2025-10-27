"""데이터 직렬화 유틸리티 - DataFrame ↔ PortData 변환."""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import pyarrow as pa

from ai_canvas_sdk.grpc import custom_node_service_pb2 as pb
from google.protobuf import struct_pb2, any_pb2
from google.protobuf.json_format import MessageToDict

logger = logging.getLogger(__name__)


class DataSerializer:
    """
    DataFrame과 gRPC PortData 간의 변환을 담당하는 클래스.

    크기에 따라 자동으로 최적의 직렬화 전략을 선택합니다:
    - 작은 데이터 (<1만 행): JSON (간편성 우선)
    - 중간 데이터 (1만~10만 행): Arrow + LZ4 압축 (성능 우선)
    - 큰 데이터 (>10만 행): 에러 반환 (파일 전송 권장)
    """

    # 임계값 설정
    SMALL_DATA_THRESHOLD = 10_000  # 1만 행
    LARGE_DATA_THRESHOLD = 100_000  # 10만 행
    GRPC_SIZE_LIMIT = 3 * 1024 * 1024  # 3MB (안전 마진)

    def serialize(self, df: pd.DataFrame, port_id: str, port_name: str = "") -> pb.PortData:
        """
        DataFrame을 PortData로 직렬화합니다.

        Args:
            df: 직렬화할 DataFrame
            port_id: 포트 ID
            port_name: 포트 이름 (선택)

        Returns:
            PortData protobuf 메시지

        Raises:
            ValueError: 데이터가 너무 큰 경우
        """
        row_count = len(df)
        logger.debug(f"Serializing DataFrame: {row_count} rows, {len(df.columns)} columns")

        # 작은 데이터 → JSON
        if row_count < self.SMALL_DATA_THRESHOLD:
            return self._serialize_as_json(df, port_id, port_name)

        # 중간/큰 데이터 → Arrow 시도
        arrow_bytes = self._to_arrow_bytes(df)
        arrow_size = len(arrow_bytes)

        logger.debug(f"Arrow serialization size: {arrow_size:,} bytes")

        if arrow_size < self.GRPC_SIZE_LIMIT:
            # gRPC 제한 내 → Arrow 바이너리
            return pb.PortData(
                port_id=port_id,
                port_name=port_name,
                port_type=pb.PORT_TYPE_DATASET,
                binary_data=arrow_bytes,
                metadata={
                    "format": "arrow",
                    "rows": str(row_count),
                    "columns": str(len(df.columns)),
                    "size_bytes": str(arrow_size),
                },
            )
        else:
            # gRPC 제한 초과 → 에러
            raise ValueError(
                f"DataFrame이 너무 큽니다 ({arrow_size:,} bytes > {self.GRPC_SIZE_LIMIT:,} bytes). "
                f"행 수: {row_count:,}, 열 수: {len(df.columns)}. "
                f"공유 볼륨 파일 전송을 사용하세요."
            )

    def _serialize_as_json(self, df: pd.DataFrame, port_id: str, port_name: str) -> pb.PortData:
        """
        DataFrame을 JSON으로 직렬화합니다.

        Args:
            df: DataFrame
            port_id: 포트 ID
            port_name: 포트 이름

        Returns:
            JSON 형식의 PortData
        """
        logger.debug("Using JSON serialization")

        # DataFrame을 dict로 변환
        data_dict = df.to_dict(orient="records")

        # dtype 정보 저장 (역직렬화 시 타입 복원용)
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

        # google.protobuf.Struct로 JSON 데이터 구성
        json_struct = struct_pb2.Struct()
        json_struct.update({
            "data": data_dict,
            "columns": df.columns.tolist(),
            "dtypes": dtypes,
        })

        # Any 타입에 Pack
        json_any = any_pb2.Any()
        json_any.Pack(json_struct)

        return pb.PortData(
            port_id=port_id,
            port_name=port_name,
            port_type=pb.PORT_TYPE_DATASET,
            json_data=json_any,
            metadata={
                "format": "json",
                "rows": str(len(df)),
                "columns": str(len(df.columns)),
            },
        )

    def _to_arrow_bytes(self, df: pd.DataFrame) -> bytes:
        """
        DataFrame을 Arrow IPC 형식으로 직렬화합니다.

        Args:
            df: DataFrame

        Returns:
            Arrow IPC 바이트 데이터 (LZ4 압축)
        """
        logger.debug("Using Arrow serialization with LZ4 compression")

        # pandas DataFrame → Arrow Table
        table = pa.Table.from_pandas(df)

        # Arrow IPC 스트림으로 직렬화 (LZ4 압축)
        sink = pa.BufferOutputStream()
        writer = pa.ipc.new_stream(
            sink, table.schema, options=pa.ipc.IpcWriteOptions(compression="lz4")
        )
        writer.write_table(table)
        writer.close()

        return sink.getvalue().to_pybytes()

    def deserialize(self, port_data: pb.PortData) -> pd.DataFrame:
        """
        PortData를 DataFrame으로 역직렬화합니다.

        metadata["format"]을 보고 자동으로 JSON/Arrow를 감지합니다.

        Args:
            port_data: PortData protobuf 메시지

        Returns:
            pandas DataFrame

        Raises:
            ValueError: 지원하지 않는 형식
        """
        format_type = port_data.metadata.get("format", "json")

        logger.debug(f"Deserializing PortData: format={format_type}")

        if format_type == "json":
            return self._deserialize_from_json(port_data)
        elif format_type == "arrow":
            return self._deserialize_from_arrow(port_data)
        else:
            raise ValueError(f"지원하지 않는 데이터 형식: {format_type}")

    def _deserialize_from_json(self, port_data: pb.PortData) -> pd.DataFrame:
        """
        JSON PortData를 DataFrame으로 변환합니다.

        Args:
            port_data: JSON 형식의 PortData

        Returns:
            pandas DataFrame
        """
        logger.debug("Deserializing from JSON")

        # Any 타입에서 Struct로 Unpack
        json_struct = struct_pb2.Struct()
        port_data.json_data.Unpack(json_struct)

        # Struct를 Python dict로 변환
        json_dict = MessageToDict(json_struct)

        data_dict = json_dict.get("data", [])
        df = pd.DataFrame(data_dict)

        # dtype 복원 시도 (선택적)
        dtypes = json_dict.get("dtypes", {})
        if dtypes:
            try:
                for col, dtype_str in dtypes.items():
                    if col in df.columns:
                        # 기본 타입만 복원 (datetime 등은 자동 추론에 맡김)
                        if dtype_str.startswith("int"):
                            df[col] = df[col].astype("int64")
                        elif dtype_str.startswith("float"):
                            df[col] = df[col].astype("float64")
            except Exception as e:
                logger.warning(f"Failed to restore dtypes: {e}")

        return df

    def _deserialize_from_arrow(self, port_data: pb.PortData) -> pd.DataFrame:
        """
        Arrow PortData를 DataFrame으로 변환합니다.

        Args:
            port_data: Arrow 형식의 PortData

        Returns:
            pandas DataFrame
        """
        logger.debug("Deserializing from Arrow")

        # Arrow IPC 스트림에서 읽기
        reader = pa.ipc.open_stream(port_data.binary_data)
        table = reader.read_all()

        # Arrow Table → pandas DataFrame
        return table.to_pandas()

    def serialize_value(self, value: Any, port_id: str, port_name: str = "") -> pb.PortData:
        """
        다양한 타입의 값을 PortData로 직렬화합니다.

        Args:
            value: 직렬화할 값 (DataFrame, dict, str 등)
            port_id: 포트 ID
            port_name: 포트 이름

        Returns:
            PortData
        """
        if isinstance(value, pd.DataFrame):
            return self.serialize(value, port_id, port_name)
        elif isinstance(value, dict):
            # dict → JSON (Struct로 감싸서 Any에 Pack)
            json_struct = struct_pb2.Struct()
            json_struct.update(value)

            json_any = any_pb2.Any()
            json_any.Pack(json_struct)

            return pb.PortData(
                port_id=port_id,
                port_name=port_name,
                port_type=pb.PORT_TYPE_JSON,
                json_data=json_any,
                metadata={"format": "json"},
            )
        elif isinstance(value, str):
            # str → text_data
            return pb.PortData(
                port_id=port_id,
                port_name=port_name,
                port_type=pb.PORT_TYPE_JSON,
                text_data=value,
                metadata={"format": "text"},
            )
        elif isinstance(value, (int, float)):
            # 숫자 → number_data
            return pb.PortData(
                port_id=port_id,
                port_name=port_name,
                port_type=pb.PORT_TYPE_JSON,
                number_data=float(value),
                metadata={"format": "number"},
            )
        elif isinstance(value, bool):
            # bool → boolean_data
            return pb.PortData(
                port_id=port_id,
                port_name=port_name,
                port_type=pb.PORT_TYPE_JSON,
                boolean_data=value,
                metadata={"format": "boolean"},
            )
        else:
            # 기타 타입 → JSON으로 변환 시도
            logger.warning(f"Unknown type {type(value)}, converting to dict")

            json_struct = struct_pb2.Struct()
            json_struct.update({"value": str(value)})

            json_any = any_pb2.Any()
            json_any.Pack(json_struct)

            return pb.PortData(
                port_id=port_id,
                port_name=port_name,
                port_type=pb.PORT_TYPE_JSON,
                json_data=json_any,
                metadata={"format": "json"},
            )

    def deserialize_value(self, port_data: pb.PortData) -> Any:
        """
        PortData를 Python 값으로 역직렬화합니다.

        Args:
            port_data: PortData

        Returns:
            Python 값 (DataFrame, dict, str 등)
        """
        format_type = port_data.metadata.get("format", "unknown")

        if port_data.port_type == pb.PORT_TYPE_DATASET or format_type in ["json", "arrow"]:
            # DataFrame
            return self.deserialize(port_data)
        elif format_type == "text" or port_data.WhichOneof("data") == "text_data":
            # 문자열
            return port_data.text_data
        elif format_type == "number" or port_data.WhichOneof("data") == "number_data":
            # 숫자
            return port_data.number_data
        elif format_type == "boolean" or port_data.WhichOneof("data") == "boolean_data":
            # bool
            return port_data.boolean_data
        elif port_data.WhichOneof("data") == "json_data":
            # dict - Any에서 Struct로 Unpack
            try:
                json_struct = struct_pb2.Struct()
                port_data.json_data.Unpack(json_struct)
                return MessageToDict(json_struct)
            except Exception as e:
                logger.warning(f"Failed to unpack json_data: {e}")
                return None
        else:
            logger.warning(f"Unknown port data type: {port_data.port_type}, format: {format_type}")
            return None
