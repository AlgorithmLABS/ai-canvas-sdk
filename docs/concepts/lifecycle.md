# 노드 생명주기

AI Canvas 커스텀 노드의 전체 생명주기와 각 단계별 처리 과정을 자세히 설명합니다.

## 🔄 노드 실행 생명주기 개요

```
📋 등록 → 🔍 검증 → 🚀 초기화 → ⚙️ 실행 → 📤 결과 반환 → 🧹 정리
  ↓         ↓         ↓         ↓         ↓            ↓
Register  Validate  Initialize Execute  Serialize   Cleanup
```

## 1️⃣ 노드 등록 단계 (Registration)

### 1.1 노드 디스커버리

```python
# SDK가 자동으로 노드 클래스를 발견하는 방법
class NodeDiscovery:
    @staticmethod
    def discover_nodes(module_path: str) -> List[Type[CustomNode]]:
        """모듈에서 CustomNode 서브클래스를 자동 발견"""
        
        import importlib.util
        import inspect
        
        spec = importlib.util.spec_from_file_location("custom_nodes", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        node_classes = []
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, CustomNode) and 
                obj != CustomNode):
                node_classes.append(obj)
        
        return node_classes

# 실제 노드 파일에서는 간단히
from aicanvas_sdk import CustomNode

class MyNode(CustomNode):  # SDK가 자동 발견
    pass

node = MyNode()  # 인스턴스 생성으로 등록 완료
```

### 1.2 스키마 검증

```python
class SchemaValidator:
    """노드 스키마 검증기"""
    
    @staticmethod
    def validate_schema(schema: NodeSchema) -> List[str]:
        """스키마 유효성 검증"""
        errors = []
        
        # 필수 필드 검증
        if not schema.name:
            errors.append("노드 이름이 필요합니다")
        
        if not schema.display_name:
            errors.append("표시 이름이 필요합니다")
        
        # 포트 검증
        for input_port in schema.inputs:
            if not input_port.get('name'):
                errors.append("입력 포트에 이름이 필요합니다")
            
            if input_port.get('type') not in PortType.__members__.values():
                errors.append(f"유효하지 않은 포트 타입: {input_port.get('type')}")
        
        # 파라미터 검증
        for param in schema.parameters:
            if param.get('type') == 'select' and not param.get('options'):
                errors.append(f"Select 파라미터 '{param.get('name')}'에 options가 필요합니다")
        
        return errors

# 등록 시 자동 실행
registration_result = {
    "node_id": "my_node_v1.0.0",
    "status": "success",
    "schema_errors": [],
    "registration_time": "2024-01-15T10:30:00Z"
}
```

## 2️⃣ 실행 준비 단계 (Pre-execution)

### 2.1 실행 컨텍스트 생성

```python
@dataclass
class ExecutionContext:
    """노드 실행 컨텍스트"""
    
    # 실행 메타정보
    execution_id: str
    node_id: str
    canvas_id: str
    user_id: str
    
    # 타이밍 정보
    start_time: datetime
    timeout_seconds: int = 300
    
    # 리소스 제한
    memory_limit_mb: int = 2048
    cpu_limit_cores: float = 1.0
    
    # 실행 옵션
    enable_profiling: bool = False
    enable_streaming: bool = None  # None = auto
    debug_mode: bool = False
    
    # 환경 변수
    environment: Dict[str, str] = field(default_factory=dict)

def create_execution_context(request) -> ExecutionContext:
    """실행 컨텍스트 생성"""
    
    return ExecutionContext(
        execution_id=generate_uuid(),
        node_id=request.node_id,
        canvas_id=request.canvas_id,
        user_id=request.user_id,
        start_time=datetime.now(),
        timeout_seconds=request.timeout or 300,
        memory_limit_mb=request.memory_limit or 2048,
        enable_profiling=request.enable_profiling or False,
        debug_mode=request.debug_mode or False
    )
```

### 2.2 데이터 역직렬화

```python
class DataDeserializer:
    """gRPC 메시지에서 Python 객체로 역직렬화"""
    
    def deserialize_inputs(self, grpc_inputs: List[PortData]) -> Dict[str, Any]:
        """입력 포트 데이터 역직렬화"""
        
        inputs = {}
        
        for port_data in grpc_inputs:
            port_name = port_data.port_name
            
            if port_data.HasField('dataframe'):
                # DataFrame 역직렬화
                df_data = port_data.dataframe
                
                if df_data.HasField('parquet_data'):
                    inputs[port_name] = self._deserialize_parquet(df_data.parquet_data)
                elif df_data.HasField('arrow_data'):
                    inputs[port_name] = self._deserialize_arrow(df_data.arrow_data)
                elif df_data.HasField('json_data'):
                    inputs[port_name] = pd.read_json(df_data.json_data, orient='split')
            
            elif port_data.HasField('model'):
                # 모델 역직렬화
                model_data = port_data.model.serialized_model
                inputs[port_name] = self._deserialize_model(model_data, port_data.model.model_type)
            
            elif port_data.HasField('json_data'):
                # JSON 데이터
                inputs[port_name] = json.loads(port_data.json_data)
            
            # ... 다른 타입들
        
        return inputs
    
    def _deserialize_parquet(self, data: bytes) -> pd.DataFrame:
        """Parquet 데이터 역직렬화"""
        return pd.read_parquet(BytesIO(data))
    
    def _deserialize_arrow(self, data: bytes) -> pd.DataFrame:
        """Arrow 데이터 역직렬화"""
        reader = pa.ipc.open_stream(BytesIO(data))
        table = reader.read_all()
        return table.to_pandas()
```

## 3️⃣ 검증 단계 (Validation)

### 3.1 입력 데이터 검증

```python
class DataValidator:
    """입력 데이터 및 파라미터 검증"""
    
    def __init__(self, schema: NodeSchema):
        self.schema = schema
    
    def validate_execution_request(self, inputs: Dict[str, Any], 
                                 parameters: Dict[str, Any]) -> List[ValidationError]:
        """실행 요청 전체 검증"""
        errors = []
        
        # 필수 입력 포트 확인
        errors.extend(self._validate_required_inputs(inputs))
        
        # 데이터 타입 검증
        errors.extend(self._validate_input_types(inputs))
        
        # 파라미터 검증
        errors.extend(self._validate_parameters(parameters))
        
        # 데이터 품질 검증
        errors.extend(self._validate_data_quality(inputs))
        
        return errors
    
    def _validate_required_inputs(self, inputs: Dict[str, Any]) -> List[ValidationError]:
        """필수 입력 포트 확인"""
        errors = []
        
        required_inputs = [port for port in self.schema.inputs if port.get('required', False)]
        
        for port in required_inputs:
            port_name = port['name']
            if port_name not in inputs or inputs[port_name] is None:
                errors.append(ValidationError(
                    field=port_name,
                    message=f"필수 입력 포트 '{port_name}'이 비어있습니다",
                    error_type="MISSING_REQUIRED_INPUT"
                ))
        
        return errors
    
    def _validate_data_quality(self, inputs: Dict[str, Any]) -> List[ValidationError]:
        """데이터 품질 검증"""
        errors = []
        
        for port_name, data in inputs.items():
            if isinstance(data, pd.DataFrame):
                # DataFrame 품질 확인
                if data.empty:
                    errors.append(ValidationError(
                        field=port_name,
                        message=f"DataFrame '{port_name}'이 비어있습니다",
                        error_type="EMPTY_DATAFRAME"
                    ))
                
                # 결측값 확인 (옵션)
                null_percentage = (data.isnull().sum().sum() / data.size) * 100
                if null_percentage > 50:  # 50% 이상 결측값
                    errors.append(ValidationError(
                        field=port_name,
                        message=f"DataFrame '{port_name}'에 결측값이 {null_percentage:.1f}% 포함되어 있습니다",
                        error_type="HIGH_NULL_PERCENTAGE"
                    ))
        
        return errors

@dataclass
class ValidationError:
    field: str
    message: str
    error_type: str
    suggestion: str = None
```

### 3.2 사용자 정의 검증

```python
# 노드 개발자가 구현하는 validate() 메서드
class MyCustomNode(CustomNode):
    def validate(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        """사용자 정의 검증 로직"""
        
        # 비즈니스 룰 검증
        df = inputs.get('customer_data')
        min_customers = parameters.get('min_customers', 100)
        
        if len(df) < min_customers:
            raise ValidationError(
                field="customer_data",
                message=f"최소 {min_customers}명의 고객 데이터가 필요합니다. 현재: {len(df)}명",
                error_type="INSUFFICIENT_DATA"
            )
        
        # 데이터 일관성 검증
        required_columns = ['customer_id', 'email', 'signup_date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(
                field="customer_data",
                message=f"필수 컬럼이 누락되었습니다: {missing_columns}",
                error_type="MISSING_COLUMNS"
            )
        
        # 데이터 무결성 검증
        if df['customer_id'].duplicated().any():
            raise ValidationError(
                field="customer_data", 
                message="customer_id에 중복값이 있습니다",
                error_type="DUPLICATE_VALUES"
            )
```

## 4️⃣ 실행 단계 (Execution)

### 4.1 실행 환경 설정

```python
class ExecutionEnvironment:
    """노드 실행 환경"""
    
    def __init__(self, context: ExecutionContext):
        self.context = context
        self.metrics = ExecutionMetrics()
        self.profiler = NodeProfiler() if context.enable_profiling else None
    
    def __enter__(self):
        """실행 환경 진입"""
        self.metrics.start_time = time.time()
        self.metrics.start_memory = self._get_memory_usage()
        
        if self.profiler:
            self.profiler.start()
        
        # 리소스 제한 설정
        self._set_resource_limits()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """실행 환경 정리"""
        self.metrics.end_time = time.time()
        self.metrics.end_memory = self._get_memory_usage()
        
        if self.profiler:
            self.profiler.stop()
            self.metrics.profile_data = self.profiler.get_results()
        
        # 예외 처리
        if exc_type:
            self.metrics.error_type = exc_type.__name__
            self.metrics.error_message = str(exc_val)
    
    def _set_resource_limits(self):
        """리소스 제한 설정"""
        import resource
        
        # 메모리 제한
        memory_limit_bytes = self.context.memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
        
        # 시간 제한 (별도 스레드에서 처리)
        threading.Timer(self.context.timeout_seconds, self._timeout_handler).start()
```

### 4.2 실제 노드 실행

```python
class NodeExecutor:
    """노드 실행 엔진"""
    
    def execute_node(self, node: CustomNode, inputs: Dict[str, Any], 
                    parameters: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """노드 실행 메인 함수"""
        
        with ExecutionEnvironment(context) as env:
            try:
                # 1. 사용자 정의 검증
                if hasattr(node, 'validate'):
                    node.validate(inputs, parameters)
                
                # 2. 실행 방식 결정
                if self._should_use_streaming(inputs, parameters):
                    return self._execute_streaming(node, inputs, parameters)
                else:
                    return self._execute_normal(node, inputs, parameters)
            
            except Exception as e:
                # 에러 정보 수집
                error_info = {
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'stack_trace': traceback.format_exc(),
                    'execution_context': context.__dict__
                }
                
                # 로깅
                logger.error("Node execution failed", extra=error_info)
                
                # 재시도 가능한 에러인지 판단
                if self._is_retryable_error(e):
                    raise RetryableNodeError(str(e)) from e
                else:
                    raise NodeExecutionError(str(e)) from e
    
    def _execute_normal(self, node: CustomNode, inputs: Dict[str, Any], 
                       parameters: Dict[str, Any]) -> Dict[str, Any]:
        """일반 실행"""
        
        logger.info(f"Executing node {node.__class__.__name__}")
        
        # 실행 시간 측정
        start_time = time.time()
        result = node.run(inputs, parameters, NodeContext())
        execution_time = time.time() - start_time
        
        logger.info(f"Node execution completed in {execution_time:.2f}s")
        
        return result
    
    def _execute_streaming(self, node: CustomNode, inputs: Dict[str, Any],
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """스트리밍 실행"""
        
        if hasattr(node, 'execute_streaming'):
            return node.execute_streaming(inputs, parameters)
        else:
            # 스트리밍을 지원하지 않는 노드는 일반 실행
            return self._execute_normal(node, inputs, parameters)
```

### 4.3 진행 상황 추적

```python
class ProgressTracker:
    """실행 진행 상황 추적"""
    
    def __init__(self, execution_id: str, websocket_sender):
        self.execution_id = execution_id
        self.websocket = websocket_sender
        self.current_step = 0
        self.total_steps = 0
    
    def set_total_steps(self, total: int):
        """전체 단계 수 설정"""
        self.total_steps = total
        self._send_progress()
    
    def advance(self, step_name: str = None):
        """다음 단계로 진행"""
        self.current_step += 1
        self._send_progress(step_name)
    
    def _send_progress(self, step_name: str = None):
        """진행 상황 전송"""
        progress_data = {
            'execution_id': self.execution_id,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'percentage': (self.current_step / self.total_steps * 100) if self.total_steps > 0 else 0,
            'step_name': step_name,
            'timestamp': datetime.now().isoformat()
        }
        
        self.websocket.send_progress(progress_data)

# 노드에서 사용 예시
class ProgressAwareNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        progress = self.get_progress_tracker()  # SDK가 제공
        
        progress.set_total_steps(4)
        
        # Step 1: 데이터 로드
        progress.advance("데이터 로딩 중...")
        data = inputs['dataset']
        
        # Step 2: 전처리
        progress.advance("데이터 전처리 중...")
        cleaned_data = self.preprocess(data)
        
        # Step 3: 분석
        progress.advance("데이터 분석 중...")
        results = self.analyze(cleaned_data)
        
        # Step 4: 완료
        progress.advance("결과 생성 중...")
        return {'results': results}
```

## 5️⃣ 결과 처리 단계 (Post-execution)

### 5.1 출력 검증

```python
class OutputValidator:
    """출력 데이터 검증"""
    
    def validate_outputs(self, outputs: Dict[str, Any], 
                        schema: NodeSchema) -> List[ValidationError]:
        """출력 데이터 검증"""
        errors = []
        
        # 필수 출력 포트 확인
        required_outputs = [port for port in schema.outputs if port.get('required', False)]
        for port in required_outputs:
            port_name = port['name']
            if port_name not in outputs:
                errors.append(ValidationError(
                    field=port_name,
                    message=f"필수 출력 포트 '{port_name}'이 누락되었습니다",
                    error_type="MISSING_REQUIRED_OUTPUT"
                ))
        
        # 출력 타입 확인
        for port_name, data in outputs.items():
            expected_type = self._get_expected_type(port_name, schema)
            if not self._validate_output_type(data, expected_type):
                errors.append(ValidationError(
                    field=port_name,
                    message=f"출력 타입이 일치하지 않습니다. 예상: {expected_type}, 실제: {type(data)}",
                    error_type="INVALID_OUTPUT_TYPE"
                ))
        
        return errors
```

### 5.2 결과 직렬화

```python
class ResultSerializer:
    """실행 결과 직렬화"""
    
    def serialize_outputs(self, outputs: Dict[str, Any]) -> List[PortData]:
        """출력 데이터를 gRPC 메시지로 직렬화"""
        
        grpc_outputs = []
        
        for port_name, data in outputs.items():
            port_data = PortData()
            port_data.port_name = port_name
            
            if isinstance(data, pd.DataFrame):
                # DataFrame 직렬화 전략 선택
                strategy = self._choose_serialization_strategy(data)
                
                if strategy == "parquet":
                    buffer = BytesIO()
                    data.to_parquet(buffer, compression='snappy')
                    port_data.dataframe.parquet_data = buffer.getvalue()
                
                elif strategy == "arrow":
                    table = pa.Table.from_pandas(data)
                    sink = pa.BufferOutputStream()
                    with pa.ipc.RecordBatchStreamWriter(sink, table.schema) as writer:
                        writer.write_table(table)
                    port_data.dataframe.arrow_data = sink.getvalue().to_pybytes()
            
            elif hasattr(data, 'predict'):  # ML 모델
                buffer = BytesIO()
                joblib.dump(data, buffer)
                port_data.model.serialized_model = buffer.getvalue()
                port_data.model.model_type = self._detect_model_type(data)
            
            elif isinstance(data, (dict, list)):
                port_data.json_data = json.dumps(data)
            
            grpc_outputs.append(port_data)
        
        return grpc_outputs
    
    def _choose_serialization_strategy(self, df: pd.DataFrame) -> str:
        """DataFrame 크기에 따른 직렬화 전략 선택"""
        memory_usage_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        if memory_usage_mb > 50:
            return "arrow"  # 대용량은 속도 우선
        else:
            return "parquet"  # 중간 크기는 압축 우선
```

## 6️⃣ 정리 단계 (Cleanup)

### 6.1 리소스 정리

```python
class ResourceManager:
    """리소스 정리 관리"""
    
    def __init__(self):
        self.resources = []
        self.temp_files = []
        self.cleanup_callbacks = []
    
    def register_resource(self, resource):
        """정리가 필요한 리소스 등록"""
        self.resources.append(resource)
    
    def register_temp_file(self, file_path: str):
        """임시 파일 등록"""
        self.temp_files.append(file_path)
    
    def register_cleanup_callback(self, callback):
        """정리 콜백 등록"""
        self.cleanup_callbacks.append(callback)
    
    def cleanup_all(self):
        """모든 리소스 정리"""
        
        # 콜백 실행
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"Cleanup callback failed: {e}")
        
        # 리소스 정리
        for resource in self.resources:
            try:
                if hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'cleanup'):
                    resource.cleanup()
            except Exception as e:
                logger.warning(f"Resource cleanup failed: {e}")
        
        # 임시 파일 삭제
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Temp file cleanup failed: {e}")

# 노드에서 사용 예시
class ResourceAwareNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        resource_manager = self.get_resource_manager()  # SDK가 제공
        
        # 대용량 데이터 처리를 위한 임시 파일 생성
        temp_file = "/tmp/large_dataset.parquet"
        large_df = inputs['large_dataset']
        large_df.to_parquet(temp_file)
        
        # 정리 대상으로 등록
        resource_manager.register_temp_file(temp_file)
        
        # 처리 로직
        result = self.process_file(temp_file)
        
        return {'result': result}
        # 실행 완료 후 SDK가 자동으로 정리
```

## 📊 실행 메트릭 수집

### 실행 통계 추적

```python
@dataclass
class ExecutionMetrics:
    """실행 통계 정보"""
    
    # 기본 정보
    execution_id: str
    node_name: str
    node_version: str
    
    # 타이밍 정보
    start_time: float = None
    end_time: float = None
    validation_time_ms: float = None
    deserialization_time_ms: float = None
    execution_time_ms: float = None
    serialization_time_ms: float = None
    
    # 리소스 사용량
    start_memory_mb: float = None
    peak_memory_mb: float = None
    end_memory_mb: float = None
    cpu_usage_percent: float = None
    
    # 데이터 정보
    input_data_size_mb: float = None
    output_data_size_mb: float = None
    
    # 에러 정보
    error_type: str = None
    error_message: str = None
    
    # 프로파일링 데이터
    profile_data: Dict = None
    
    def get_total_time_ms(self) -> float:
        """전체 실행 시간 계산"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None
    
    def get_memory_delta_mb(self) -> float:
        """메모리 사용량 변화"""
        if self.start_memory_mb and self.end_memory_mb:
            return self.end_memory_mb - self.start_memory_mb
        return None

# 메트릭 수집 예시
def collect_execution_metrics(execution_context, results):
    """실행 메트릭 수집 및 전송"""
    
    metrics = ExecutionMetrics(
        execution_id=execution_context.execution_id,
        node_name=execution_context.node_name,
        node_version=execution_context.node_version
    )
    
    # AI Canvas Backend로 메트릭 전송
    send_metrics_to_backend(metrics)
```

## 🔄 에러 복구 및 재시도

### 재시도 로직

```python
class RetryHandler:
    """노드 실행 재시도 처리"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_delays = [1, 2, 5]  # 지수적 백오프
    
    def execute_with_retry(self, node: CustomNode, inputs: Dict[str, Any],
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """재시도를 포함한 노드 실행"""
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return node.run(inputs, parameters, NodeContext())
            
            except RetryableNodeError as e:
                last_error = e
                
                if attempt < self.max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.warning(f"Node execution failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Node execution failed after {self.max_retries} retries")
                    
            except NodeExecutionError as e:
                # 재시도 불가능한 에러
                logger.error(f"Non-retryable error: {e}")
                raise
        
        # 모든 재시도 실패
        raise NodeExecutionError(f"Execution failed after {self.max_retries} retries") from last_error
```

---

이러한 **체계적인 생명주기 관리**를 통해 노드 실행의 **안정성**, **성능**, **디버깅 가능성**을 모두 보장할 수 있습니다.