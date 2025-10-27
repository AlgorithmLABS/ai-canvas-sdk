import datetime

from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProgressStage(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STAGE_UNKNOWN: _ClassVar[ProgressStage]
    STAGE_INITIALIZING: _ClassVar[ProgressStage]
    STAGE_LOADING_DATA: _ClassVar[ProgressStage]
    STAGE_PROCESSING: _ClassVar[ProgressStage]
    STAGE_SAVING_RESULTS: _ClassVar[ProgressStage]
    STAGE_CLEANING_UP: _ClassVar[ProgressStage]
    STAGE_COMPLETED: _ClassVar[ProgressStage]
    STAGE_FAILED: _ClassVar[ProgressStage]
    STAGE_CANCELLED: _ClassVar[ProgressStage]

class PortType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PORT_TYPE_UNKNOWN: _ClassVar[PortType]
    PORT_TYPE_DATASET: _ClassVar[PortType]
    PORT_TYPE_UNTRAINED: _ClassVar[PortType]
    PORT_TYPE_TRAINED: _ClassVar[PortType]
    PORT_TYPE_TRANSFORMER: _ClassVar[PortType]
    PORT_TYPE_DISPLAY: _ClassVar[PortType]
    PORT_TYPE_SCORED_DATASET: _ClassVar[PortType]
    PORT_TYPE_JSON: _ClassVar[PortType]

class CompressionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COMPRESSION_NONE: _ClassVar[CompressionType]
    COMPRESSION_GZIP: _ClassVar[CompressionType]
    COMPRESSION_SNAPPY: _ClassVar[CompressionType]
    COMPRESSION_LZ4: _ClassVar[CompressionType]
    COMPRESSION_ZSTD: _ClassVar[CompressionType]

class ExecutionState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXECUTION_STATE_UNKNOWN: _ClassVar[ExecutionState]
    EXECUTION_STATE_PENDING: _ClassVar[ExecutionState]
    EXECUTION_STATE_RUNNING: _ClassVar[ExecutionState]
    EXECUTION_STATE_SUCCESS: _ClassVar[ExecutionState]
    EXECUTION_STATE_FAILED: _ClassVar[ExecutionState]
    EXECUTION_STATE_CANCELLED: _ClassVar[ExecutionState]
    EXECUTION_STATE_TIMEOUT: _ClassVar[ExecutionState]

class LogLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LOG_LEVEL_UNKNOWN: _ClassVar[LogLevel]
    LOG_LEVEL_DEBUG: _ClassVar[LogLevel]
    LOG_LEVEL_INFO: _ClassVar[LogLevel]
    LOG_LEVEL_WARNING: _ClassVar[LogLevel]
    LOG_LEVEL_ERROR: _ClassVar[LogLevel]
    LOG_LEVEL_CRITICAL: _ClassVar[LogLevel]

class ErrorCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ERROR_CODE_UNKNOWN: _ClassVar[ErrorCode]
    ERROR_CODE_INVALID_INPUT: _ClassVar[ErrorCode]
    ERROR_CODE_INVALID_PARAMETERS: _ClassVar[ErrorCode]
    ERROR_CODE_NODE_NOT_FOUND: _ClassVar[ErrorCode]
    ERROR_CODE_EXECUTION_TIMEOUT: _ClassVar[ErrorCode]
    ERROR_CODE_INSUFFICIENT_RESOURCES: _ClassVar[ErrorCode]
    ERROR_CODE_PERMISSION_DENIED: _ClassVar[ErrorCode]
    ERROR_CODE_DATA_SERIALIZATION_ERROR: _ClassVar[ErrorCode]
    ERROR_CODE_FILE_NOT_FOUND: _ClassVar[ErrorCode]
    ERROR_CODE_NETWORK_ERROR: _ClassVar[ErrorCode]
    ERROR_CODE_INTERNAL_ERROR: _ClassVar[ErrorCode]

class SchemaType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SCHEMA_TYPE_UNKNOWN: _ClassVar[SchemaType]
    SCHEMA_TYPE_TABULAR: _ClassVar[SchemaType]
    SCHEMA_TYPE_MODEL: _ClassVar[SchemaType]
    SCHEMA_TYPE_IMAGE: _ClassVar[SchemaType]
    SCHEMA_TYPE_TEXT: _ClassVar[SchemaType]
    SCHEMA_TYPE_JSON: _ClassVar[SchemaType]
    SCHEMA_TYPE_BINARY: _ClassVar[SchemaType]

class DataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DATA_TYPE_UNKNOWN: _ClassVar[DataType]
    DATA_TYPE_STRING: _ClassVar[DataType]
    DATA_TYPE_INTEGER: _ClassVar[DataType]
    DATA_TYPE_FLOAT: _ClassVar[DataType]
    DATA_TYPE_BOOLEAN: _ClassVar[DataType]
    DATA_TYPE_DATETIME: _ClassVar[DataType]
    DATA_TYPE_CATEGORICAL: _ClassVar[DataType]
    DATA_TYPE_BINARY: _ClassVar[DataType]

class HealthStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HEALTH_STATUS_UNKNOWN: _ClassVar[HealthStatus]
    HEALTH_STATUS_HEALTHY: _ClassVar[HealthStatus]
    HEALTH_STATUS_DEGRADED: _ClassVar[HealthStatus]
    HEALTH_STATUS_UNHEALTHY: _ClassVar[HealthStatus]
STAGE_UNKNOWN: ProgressStage
STAGE_INITIALIZING: ProgressStage
STAGE_LOADING_DATA: ProgressStage
STAGE_PROCESSING: ProgressStage
STAGE_SAVING_RESULTS: ProgressStage
STAGE_CLEANING_UP: ProgressStage
STAGE_COMPLETED: ProgressStage
STAGE_FAILED: ProgressStage
STAGE_CANCELLED: ProgressStage
PORT_TYPE_UNKNOWN: PortType
PORT_TYPE_DATASET: PortType
PORT_TYPE_UNTRAINED: PortType
PORT_TYPE_TRAINED: PortType
PORT_TYPE_TRANSFORMER: PortType
PORT_TYPE_DISPLAY: PortType
PORT_TYPE_SCORED_DATASET: PortType
PORT_TYPE_JSON: PortType
COMPRESSION_NONE: CompressionType
COMPRESSION_GZIP: CompressionType
COMPRESSION_SNAPPY: CompressionType
COMPRESSION_LZ4: CompressionType
COMPRESSION_ZSTD: CompressionType
EXECUTION_STATE_UNKNOWN: ExecutionState
EXECUTION_STATE_PENDING: ExecutionState
EXECUTION_STATE_RUNNING: ExecutionState
EXECUTION_STATE_SUCCESS: ExecutionState
EXECUTION_STATE_FAILED: ExecutionState
EXECUTION_STATE_CANCELLED: ExecutionState
EXECUTION_STATE_TIMEOUT: ExecutionState
LOG_LEVEL_UNKNOWN: LogLevel
LOG_LEVEL_DEBUG: LogLevel
LOG_LEVEL_INFO: LogLevel
LOG_LEVEL_WARNING: LogLevel
LOG_LEVEL_ERROR: LogLevel
LOG_LEVEL_CRITICAL: LogLevel
ERROR_CODE_UNKNOWN: ErrorCode
ERROR_CODE_INVALID_INPUT: ErrorCode
ERROR_CODE_INVALID_PARAMETERS: ErrorCode
ERROR_CODE_NODE_NOT_FOUND: ErrorCode
ERROR_CODE_EXECUTION_TIMEOUT: ErrorCode
ERROR_CODE_INSUFFICIENT_RESOURCES: ErrorCode
ERROR_CODE_PERMISSION_DENIED: ErrorCode
ERROR_CODE_DATA_SERIALIZATION_ERROR: ErrorCode
ERROR_CODE_FILE_NOT_FOUND: ErrorCode
ERROR_CODE_NETWORK_ERROR: ErrorCode
ERROR_CODE_INTERNAL_ERROR: ErrorCode
SCHEMA_TYPE_UNKNOWN: SchemaType
SCHEMA_TYPE_TABULAR: SchemaType
SCHEMA_TYPE_MODEL: SchemaType
SCHEMA_TYPE_IMAGE: SchemaType
SCHEMA_TYPE_TEXT: SchemaType
SCHEMA_TYPE_JSON: SchemaType
SCHEMA_TYPE_BINARY: SchemaType
DATA_TYPE_UNKNOWN: DataType
DATA_TYPE_STRING: DataType
DATA_TYPE_INTEGER: DataType
DATA_TYPE_FLOAT: DataType
DATA_TYPE_BOOLEAN: DataType
DATA_TYPE_DATETIME: DataType
DATA_TYPE_CATEGORICAL: DataType
DATA_TYPE_BINARY: DataType
HEALTH_STATUS_UNKNOWN: HealthStatus
HEALTH_STATUS_HEALTHY: HealthStatus
HEALTH_STATUS_DEGRADED: HealthStatus
HEALTH_STATUS_UNHEALTHY: HealthStatus

class NodeRequest(_message.Message):
    __slots__ = ("execution_id", "node_id", "node_type", "node_version", "direct_inputs", "file_inputs", "parameters", "options", "security")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ParameterValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ParameterValue, _Mapping]] = ...) -> None: ...
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_TYPE_FIELD_NUMBER: _ClassVar[int]
    NODE_VERSION_FIELD_NUMBER: _ClassVar[int]
    DIRECT_INPUTS_FIELD_NUMBER: _ClassVar[int]
    FILE_INPUTS_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    SECURITY_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    node_id: str
    node_type: str
    node_version: str
    direct_inputs: _containers.RepeatedCompositeFieldContainer[PortData]
    file_inputs: _containers.RepeatedCompositeFieldContainer[FileReference]
    parameters: _containers.MessageMap[str, ParameterValue]
    options: ExecutionOptions
    security: SecurityContext
    def __init__(self, execution_id: _Optional[str] = ..., node_id: _Optional[str] = ..., node_type: _Optional[str] = ..., node_version: _Optional[str] = ..., direct_inputs: _Optional[_Iterable[_Union[PortData, _Mapping]]] = ..., file_inputs: _Optional[_Iterable[_Union[FileReference, _Mapping]]] = ..., parameters: _Optional[_Mapping[str, ParameterValue]] = ..., options: _Optional[_Union[ExecutionOptions, _Mapping]] = ..., security: _Optional[_Union[SecurityContext, _Mapping]] = ...) -> None: ...

class NodeResponse(_message.Message):
    __slots__ = ("execution_id", "status", "direct_outputs", "file_outputs", "metrics", "logs", "error")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DIRECT_OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    FILE_OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    LOGS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    status: ExecutionStatus
    direct_outputs: _containers.RepeatedCompositeFieldContainer[PortData]
    file_outputs: _containers.RepeatedCompositeFieldContainer[FileReference]
    metrics: ExecutionMetrics
    logs: _containers.RepeatedCompositeFieldContainer[LogEntry]
    error: ExecutionError
    def __init__(self, execution_id: _Optional[str] = ..., status: _Optional[_Union[ExecutionStatus, _Mapping]] = ..., direct_outputs: _Optional[_Iterable[_Union[PortData, _Mapping]]] = ..., file_outputs: _Optional[_Iterable[_Union[FileReference, _Mapping]]] = ..., metrics: _Optional[_Union[ExecutionMetrics, _Mapping]] = ..., logs: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ..., error: _Optional[_Union[ExecutionError, _Mapping]] = ...) -> None: ...

class NodeProgress(_message.Message):
    __slots__ = ("execution_id", "progress_percentage", "status_message", "stage", "log_entry", "partial_result", "current_metrics", "timestamp")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    STATUS_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STAGE_FIELD_NUMBER: _ClassVar[int]
    LOG_ENTRY_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_RESULT_FIELD_NUMBER: _ClassVar[int]
    CURRENT_METRICS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    progress_percentage: float
    status_message: str
    stage: ProgressStage
    log_entry: LogEntry
    partial_result: PartialResult
    current_metrics: ExecutionMetrics
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, execution_id: _Optional[str] = ..., progress_percentage: _Optional[float] = ..., status_message: _Optional[str] = ..., stage: _Optional[_Union[ProgressStage, str]] = ..., log_entry: _Optional[_Union[LogEntry, _Mapping]] = ..., partial_result: _Optional[_Union[PartialResult, _Mapping]] = ..., current_metrics: _Optional[_Union[ExecutionMetrics, _Mapping]] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class PortData(_message.Message):
    __slots__ = ("port_id", "port_name", "port_type", "text_data", "binary_data", "json_data", "number_data", "boolean_data", "structured_data", "metadata", "size_bytes", "checksum")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PORT_ID_FIELD_NUMBER: _ClassVar[int]
    PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    PORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TEXT_DATA_FIELD_NUMBER: _ClassVar[int]
    BINARY_DATA_FIELD_NUMBER: _ClassVar[int]
    JSON_DATA_FIELD_NUMBER: _ClassVar[int]
    NUMBER_DATA_FIELD_NUMBER: _ClassVar[int]
    BOOLEAN_DATA_FIELD_NUMBER: _ClassVar[int]
    STRUCTURED_DATA_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    port_id: str
    port_name: str
    port_type: PortType
    text_data: str
    binary_data: bytes
    json_data: _any_pb2.Any
    number_data: float
    boolean_data: bool
    structured_data: StructuredData
    metadata: _containers.ScalarMap[str, str]
    size_bytes: int
    checksum: str
    def __init__(self, port_id: _Optional[str] = ..., port_name: _Optional[str] = ..., port_type: _Optional[_Union[PortType, str]] = ..., text_data: _Optional[str] = ..., binary_data: _Optional[bytes] = ..., json_data: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., number_data: _Optional[float] = ..., boolean_data: bool = ..., structured_data: _Optional[_Union[StructuredData, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ..., size_bytes: _Optional[int] = ..., checksum: _Optional[str] = ...) -> None: ...

class FileReference(_message.Message):
    __slots__ = ("port_id", "port_name", "port_type", "file_path", "format", "size_bytes", "checksum", "compression", "schema", "metadata", "created_at")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PORT_ID_FIELD_NUMBER: _ClassVar[int]
    PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    PORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    port_id: str
    port_name: str
    port_type: PortType
    file_path: str
    format: str
    size_bytes: int
    checksum: str
    compression: CompressionType
    schema: DataSchema
    metadata: _containers.ScalarMap[str, str]
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, port_id: _Optional[str] = ..., port_name: _Optional[str] = ..., port_type: _Optional[_Union[PortType, str]] = ..., file_path: _Optional[str] = ..., format: _Optional[str] = ..., size_bytes: _Optional[int] = ..., checksum: _Optional[str] = ..., compression: _Optional[_Union[CompressionType, str]] = ..., schema: _Optional[_Union[DataSchema, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ParameterValue(_message.Message):
    __slots__ = ("string_value", "number_value", "boolean_value", "json_value", "binary_value")
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    NUMBER_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOLEAN_VALUE_FIELD_NUMBER: _ClassVar[int]
    JSON_VALUE_FIELD_NUMBER: _ClassVar[int]
    BINARY_VALUE_FIELD_NUMBER: _ClassVar[int]
    string_value: str
    number_value: float
    boolean_value: bool
    json_value: _any_pb2.Any
    binary_value: bytes
    def __init__(self, string_value: _Optional[str] = ..., number_value: _Optional[float] = ..., boolean_value: bool = ..., json_value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., binary_value: _Optional[bytes] = ...) -> None: ...

class ExecutionOptions(_message.Message):
    __slots__ = ("timeout", "heartbeat_interval", "max_memory_bytes", "max_cpu_cores", "enable_streaming", "enable_progress_reporting", "enable_partial_results", "idempotency_key", "enable_caching", "debug_mode", "log_level")
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    MAX_MEMORY_BYTES_FIELD_NUMBER: _ClassVar[int]
    MAX_CPU_CORES_FIELD_NUMBER: _ClassVar[int]
    ENABLE_STREAMING_FIELD_NUMBER: _ClassVar[int]
    ENABLE_PROGRESS_REPORTING_FIELD_NUMBER: _ClassVar[int]
    ENABLE_PARTIAL_RESULTS_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    ENABLE_CACHING_FIELD_NUMBER: _ClassVar[int]
    DEBUG_MODE_FIELD_NUMBER: _ClassVar[int]
    LOG_LEVEL_FIELD_NUMBER: _ClassVar[int]
    timeout: _duration_pb2.Duration
    heartbeat_interval: _duration_pb2.Duration
    max_memory_bytes: int
    max_cpu_cores: int
    enable_streaming: bool
    enable_progress_reporting: bool
    enable_partial_results: bool
    idempotency_key: str
    enable_caching: bool
    debug_mode: bool
    log_level: LogLevel
    def __init__(self, timeout: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., heartbeat_interval: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., max_memory_bytes: _Optional[int] = ..., max_cpu_cores: _Optional[int] = ..., enable_streaming: bool = ..., enable_progress_reporting: bool = ..., enable_partial_results: bool = ..., idempotency_key: _Optional[str] = ..., enable_caching: bool = ..., debug_mode: bool = ..., log_level: _Optional[_Union[LogLevel, str]] = ...) -> None: ...

class SecurityContext(_message.Message):
    __slots__ = ("user_id", "team_id", "permissions", "credentials")
    class CredentialsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TEAM_ID_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    CREDENTIALS_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    team_id: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    credentials: _containers.ScalarMap[str, str]
    def __init__(self, user_id: _Optional[str] = ..., team_id: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ..., credentials: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ExecutionStatus(_message.Message):
    __slots__ = ("execution_id", "state", "status_message", "started_at", "completed_at", "elapsed_time")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    STATUS_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STARTED_AT_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_AT_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_TIME_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    state: ExecutionState
    status_message: str
    started_at: _timestamp_pb2.Timestamp
    completed_at: _timestamp_pb2.Timestamp
    elapsed_time: _duration_pb2.Duration
    def __init__(self, execution_id: _Optional[str] = ..., state: _Optional[_Union[ExecutionState, str]] = ..., status_message: _Optional[str] = ..., started_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., completed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., elapsed_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class ExecutionMetrics(_message.Message):
    __slots__ = ("memory_used_bytes", "memory_peak_bytes", "cpu_usage_percent", "bytes_read", "bytes_written", "files_read", "files_written", "initialization_time", "processing_time", "serialization_time", "total_time", "custom_metrics")
    class CustomMetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    MEMORY_USED_BYTES_FIELD_NUMBER: _ClassVar[int]
    MEMORY_PEAK_BYTES_FIELD_NUMBER: _ClassVar[int]
    CPU_USAGE_PERCENT_FIELD_NUMBER: _ClassVar[int]
    BYTES_READ_FIELD_NUMBER: _ClassVar[int]
    BYTES_WRITTEN_FIELD_NUMBER: _ClassVar[int]
    FILES_READ_FIELD_NUMBER: _ClassVar[int]
    FILES_WRITTEN_FIELD_NUMBER: _ClassVar[int]
    INITIALIZATION_TIME_FIELD_NUMBER: _ClassVar[int]
    PROCESSING_TIME_FIELD_NUMBER: _ClassVar[int]
    SERIALIZATION_TIME_FIELD_NUMBER: _ClassVar[int]
    TOTAL_TIME_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_METRICS_FIELD_NUMBER: _ClassVar[int]
    memory_used_bytes: int
    memory_peak_bytes: int
    cpu_usage_percent: float
    bytes_read: int
    bytes_written: int
    files_read: int
    files_written: int
    initialization_time: _duration_pb2.Duration
    processing_time: _duration_pb2.Duration
    serialization_time: _duration_pb2.Duration
    total_time: _duration_pb2.Duration
    custom_metrics: _containers.ScalarMap[str, float]
    def __init__(self, memory_used_bytes: _Optional[int] = ..., memory_peak_bytes: _Optional[int] = ..., cpu_usage_percent: _Optional[float] = ..., bytes_read: _Optional[int] = ..., bytes_written: _Optional[int] = ..., files_read: _Optional[int] = ..., files_written: _Optional[int] = ..., initialization_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., processing_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., serialization_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., total_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., custom_metrics: _Optional[_Mapping[str, float]] = ...) -> None: ...

class LogEntry(_message.Message):
    __slots__ = ("timestamp", "level", "message", "logger_name", "thread_name", "context", "exception")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    LOGGER_NAME_FIELD_NUMBER: _ClassVar[int]
    THREAD_NAME_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    EXCEPTION_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    level: LogLevel
    message: str
    logger_name: str
    thread_name: str
    context: _containers.ScalarMap[str, str]
    exception: ExceptionInfo
    def __init__(self, timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., level: _Optional[_Union[LogLevel, str]] = ..., message: _Optional[str] = ..., logger_name: _Optional[str] = ..., thread_name: _Optional[str] = ..., context: _Optional[_Mapping[str, str]] = ..., exception: _Optional[_Union[ExceptionInfo, _Mapping]] = ...) -> None: ...

class ExceptionInfo(_message.Message):
    __slots__ = ("exception_type", "exception_message", "stack_trace", "cause")
    EXCEPTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    EXCEPTION_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STACK_TRACE_FIELD_NUMBER: _ClassVar[int]
    CAUSE_FIELD_NUMBER: _ClassVar[int]
    exception_type: str
    exception_message: str
    stack_trace: _containers.RepeatedScalarFieldContainer[str]
    cause: ExceptionInfo
    def __init__(self, exception_type: _Optional[str] = ..., exception_message: _Optional[str] = ..., stack_trace: _Optional[_Iterable[str]] = ..., cause: _Optional[_Union[ExceptionInfo, _Mapping]] = ...) -> None: ...

class ExecutionError(_message.Message):
    __slots__ = ("error_code", "error_message", "user_message", "exception", "error_context", "recovery_suggestion")
    class ErrorContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USER_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    EXCEPTION_FIELD_NUMBER: _ClassVar[int]
    ERROR_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    RECOVERY_SUGGESTION_FIELD_NUMBER: _ClassVar[int]
    error_code: ErrorCode
    error_message: str
    user_message: str
    exception: ExceptionInfo
    error_context: _containers.ScalarMap[str, str]
    recovery_suggestion: str
    def __init__(self, error_code: _Optional[_Union[ErrorCode, str]] = ..., error_message: _Optional[str] = ..., user_message: _Optional[str] = ..., exception: _Optional[_Union[ExceptionInfo, _Mapping]] = ..., error_context: _Optional[_Mapping[str, str]] = ..., recovery_suggestion: _Optional[str] = ...) -> None: ...

class PortSchema(_message.Message):
    __slots__ = ("type", "position", "port_type", "label", "required")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    PORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_FIELD_NUMBER: _ClassVar[int]
    type: str
    position: str
    port_type: PortType
    label: str
    required: bool
    def __init__(self, type: _Optional[str] = ..., position: _Optional[str] = ..., port_type: _Optional[_Union[PortType, str]] = ..., label: _Optional[str] = ..., required: bool = ...) -> None: ...

class ParameterSchema(_message.Message):
    __slots__ = ("text", "name", "form_type", "value", "value_type", "mode", "options", "is_tab")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    FORM_TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    VALUE_TYPE_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    IS_TAB_FIELD_NUMBER: _ClassVar[int]
    text: str
    name: str
    form_type: str
    value: _any_pb2.Any
    value_type: str
    mode: _any_pb2.Any
    options: _any_pb2.Any
    is_tab: bool
    def __init__(self, text: _Optional[str] = ..., name: _Optional[str] = ..., form_type: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., value_type: _Optional[str] = ..., mode: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., options: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., is_tab: bool = ...) -> None: ...

class NodeData(_message.Message):
    __slots__ = ("input_ports", "output_ports", "params")
    INPUT_PORTS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORTS_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    input_ports: _containers.RepeatedCompositeFieldContainer[PortSchema]
    output_ports: _containers.RepeatedCompositeFieldContainer[PortSchema]
    params: _containers.RepeatedCompositeFieldContainer[ParameterSchema]
    def __init__(self, input_ports: _Optional[_Iterable[_Union[PortSchema, _Mapping]]] = ..., output_ports: _Optional[_Iterable[_Union[PortSchema, _Mapping]]] = ..., params: _Optional[_Iterable[_Union[ParameterSchema, _Mapping]]] = ...) -> None: ...

class NodeDefinition(_message.Message):
    __slots__ = ("name", "data", "category", "width", "height", "version", "metadata", "source_code", "entry_class", "dependencies")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    SOURCE_CODE_FIELD_NUMBER: _ClassVar[int]
    ENTRY_CLASS_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    name: str
    data: NodeData
    category: str
    width: int
    height: int
    version: str
    metadata: NodeMetadata
    source_code: str
    entry_class: str
    dependencies: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., data: _Optional[_Union[NodeData, _Mapping]] = ..., category: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., version: _Optional[str] = ..., metadata: _Optional[_Union[NodeMetadata, _Mapping]] = ..., source_code: _Optional[str] = ..., entry_class: _Optional[str] = ..., dependencies: _Optional[_Iterable[str]] = ...) -> None: ...

class DataSchema(_message.Message):
    __slots__ = ("schema_type", "columns", "properties")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _any_pb2.Any
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
    SCHEMA_TYPE_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    schema_type: SchemaType
    columns: _containers.RepeatedCompositeFieldContainer[ColumnSchema]
    properties: _containers.MessageMap[str, _any_pb2.Any]
    def __init__(self, schema_type: _Optional[_Union[SchemaType, str]] = ..., columns: _Optional[_Iterable[_Union[ColumnSchema, _Mapping]]] = ..., properties: _Optional[_Mapping[str, _any_pb2.Any]] = ...) -> None: ...

class ColumnSchema(_message.Message):
    __slots__ = ("name", "data_type", "nullable", "default_value", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    NULLABLE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    data_type: DataType
    nullable: bool
    default_value: _any_pb2.Any
    description: str
    def __init__(self, name: _Optional[str] = ..., data_type: _Optional[_Union[DataType, str]] = ..., nullable: bool = ..., default_value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., description: _Optional[str] = ...) -> None: ...

class StructuredData(_message.Message):
    __slots__ = ("fields",)
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[StructuredField]
    def __init__(self, fields: _Optional[_Iterable[_Union[StructuredField, _Mapping]]] = ...) -> None: ...

class StructuredField(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: _any_pb2.Any
    def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class PartialResult(_message.Message):
    __slots__ = ("result_id", "result_type", "result_data", "completion_percentage", "timestamp")
    RESULT_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESULT_DATA_FIELD_NUMBER: _ClassVar[int]
    COMPLETION_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    result_id: str
    result_type: str
    result_data: _any_pb2.Any
    completion_percentage: float
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, result_id: _Optional[str] = ..., result_type: _Optional[str] = ..., result_data: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., completion_percentage: _Optional[float] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class NodeMetadata(_message.Message):
    __slots__ = ("author", "license", "documentation_url", "source_code_url", "custom_metadata", "created_at", "updated_at")
    class CustomMetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    LICENSE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENTATION_URL_FIELD_NUMBER: _ClassVar[int]
    SOURCE_CODE_URL_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_METADATA_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    author: str
    license: str
    documentation_url: str
    source_code_url: str
    custom_metadata: _containers.ScalarMap[str, str]
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, author: _Optional[str] = ..., license: _Optional[str] = ..., documentation_url: _Optional[str] = ..., source_code_url: _Optional[str] = ..., custom_metadata: _Optional[_Mapping[str, str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class RegistrationResult(_message.Message):
    __slots__ = ("success", "message", "node_name", "validation_errors")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NODE_NAME_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_ERRORS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    node_name: str
    validation_errors: _containers.RepeatedCompositeFieldContainer[ValidationError]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., node_name: _Optional[str] = ..., validation_errors: _Optional[_Iterable[_Union[ValidationError, _Mapping]]] = ...) -> None: ...

class ValidationError(_message.Message):
    __slots__ = ("field", "error_code", "error_message")
    FIELD_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    field: str
    error_code: str
    error_message: str
    def __init__(self, field: _Optional[str] = ..., error_code: _Optional[str] = ..., error_message: _Optional[str] = ...) -> None: ...

class HealthRequest(_message.Message):
    __slots__ = ("include_details",)
    INCLUDE_DETAILS_FIELD_NUMBER: _ClassVar[int]
    include_details: bool
    def __init__(self, include_details: bool = ...) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ("status", "message", "details", "timestamp")
    class DetailsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    status: HealthStatus
    message: str
    details: _containers.ScalarMap[str, str]
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, status: _Optional[_Union[HealthStatus, str]] = ..., message: _Optional[str] = ..., details: _Optional[_Mapping[str, str]] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CancelRequest(_message.Message):
    __slots__ = ("execution_id", "force")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    force: bool
    def __init__(self, execution_id: _Optional[str] = ..., force: bool = ...) -> None: ...

class CancelResponse(_message.Message):
    __slots__ = ("cancelled", "message")
    CANCELLED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    cancelled: bool
    message: str
    def __init__(self, cancelled: bool = ..., message: _Optional[str] = ...) -> None: ...

class StatusRequest(_message.Message):
    __slots__ = ("execution_id", "include_metrics", "include_logs")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_METRICS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_LOGS_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    include_metrics: bool
    include_logs: bool
    def __init__(self, execution_id: _Optional[str] = ..., include_metrics: bool = ..., include_logs: bool = ...) -> None: ...

class ListNodesRequest(_message.Message):
    __slots__ = ("category", "page", "page_size")
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    category: str
    page: int
    page_size: int
    def __init__(self, category: _Optional[str] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ...) -> None: ...

class ListNodesResponse(_message.Message):
    __slots__ = ("nodes", "total_count", "page", "page_size")
    NODES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeDefinition]
    total_count: int
    page: int
    page_size: int
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeDefinition, _Mapping]]] = ..., total_count: _Optional[int] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ...) -> None: ...

class DeleteNodeRequest(_message.Message):
    __slots__ = ("node_name", "version", "force")
    NODE_NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    node_name: str
    version: str
    force: bool
    def __init__(self, node_name: _Optional[str] = ..., version: _Optional[str] = ..., force: bool = ...) -> None: ...

class DeleteNodeResponse(_message.Message):
    __slots__ = ("success", "message", "deleted_versions")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DELETED_VERSIONS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    deleted_versions: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., deleted_versions: _Optional[_Iterable[str]] = ...) -> None: ...

class SchemaExtractionRequest(_message.Message):
    __slots__ = ("source_code", "entry_class", "dependencies", "version")
    SOURCE_CODE_FIELD_NUMBER: _ClassVar[int]
    ENTRY_CLASS_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    source_code: str
    entry_class: str
    dependencies: _containers.RepeatedScalarFieldContainer[str]
    version: str
    def __init__(self, source_code: _Optional[str] = ..., entry_class: _Optional[str] = ..., dependencies: _Optional[_Iterable[str]] = ..., version: _Optional[str] = ...) -> None: ...

class SchemaExtractionResponse(_message.Message):
    __slots__ = ("success", "schema", "validation_errors", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_ERRORS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    schema: NodeDefinition
    validation_errors: _containers.RepeatedCompositeFieldContainer[ValidationError]
    message: str
    def __init__(self, success: bool = ..., schema: _Optional[_Union[NodeDefinition, _Mapping]] = ..., validation_errors: _Optional[_Iterable[_Union[ValidationError, _Mapping]]] = ..., message: _Optional[str] = ...) -> None: ...
