# FAQ 및 문제 해결

AI Canvas Custom Node SDK 사용 시 자주 발생하는 문제와 해결 방법을 정리했습니다.

## 🚨 일반적인 문제들

### Q1: "DataFrame too large" 에러가 발생해요

**문제**: 대용량 DataFrame 처리 시 메모리 부족 에러 발생

**해결 방법**:

```python
# 문제가 되는 코드
def run(self, inputs, parameters, ctx: NodeContext):
    large_df = inputs['large_dataset']  # 100MB+
    result = large_df.copy()  # 메모리 2배 사용!
    return {'output': result}

# 해결 방법 1: 스트리밍 처리
def run(self, inputs, parameters, ctx: NodeContext):
    large_df = inputs['large_dataset']
    
    # 청크 단위 처리
    chunks = []
    chunk_size = 10000
    
    for i in range(0, len(large_df), chunk_size):
        chunk = large_df.iloc[i:i+chunk_size]
        processed_chunk = self.process_chunk(chunk)
        chunks.append(processed_chunk)
    
    result = pd.concat(chunks, ignore_index=True)
    return {'output': result}

# 해결 방법 2: 메모리 효율적 처리
def run(self, inputs, parameters, ctx: NodeContext):
    df = inputs['large_dataset']
    
    # 복사 대신 직접 수정
    df['new_column'] = df['existing_column'] * 2
    
    # 필요한 컬럼만 선택
    result = df[['col1', 'col2', 'new_column']]
    
    return {'output': result}
```

**추가 팁**:
- 10MB 이상 데이터는 자동 스트리밍 모드 사용
- `df.memory_usage(deep=True)`로 실제 메모리 사용량 확인
- 불필요한 컬럼 제거로 메모리 절약

---

### Q2: gRPC timeout 에러가 계속 발생해요

**문제**: 노드 실행 시간이 길어서 timeout 발생

**해결 방법**:

```python
# 방법 1: 노드에 timeout 설정 추가
@timeout(seconds=600)  # 10분으로 연장
class LongRunningNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        # 오래 걸리는 작업
        pass

# 방법 2: 진행 상황 업데이트
class ProgressiveNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        progress = self.get_progress_tracker()
        
        progress.set_total_steps(5)
        
        # 단계별 진행 상황 전송
        progress.advance("데이터 로딩...")
        data = self.load_data(inputs)
        
        progress.advance("전처리 중...")
        clean_data = self.preprocess(data)
        
        progress.advance("분석 중...")
        results = self.analyze(clean_data)
        
        progress.advance("완료")
        return {'results': results}

# 방법 3: 작업 분할
class ChunkedProcessingNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        large_task = inputs['large_dataset']
        
        # 작은 단위로 분할 처리
        results = []
        for chunk in self.split_into_chunks(large_task):
            chunk_result = self.process_chunk(chunk)
            results.append(chunk_result)
            
            # 중간 결과를 즉시 전송 (선택사항)
            self.send_intermediate_result(chunk_result)
        
        return {'final_result': self.combine_results(results)}
```

---

### Q3: "Column not found" 에러가 자주 나와요

**문제**: DataFrame 컬럼 접근 시 KeyError 발생

**해결 방법**:

```python
# 문제가 되는 코드
def run(self, inputs, parameters, ctx: NodeContext):
    df = inputs['data']
    result = df['missing_column']  # KeyError 발생 가능
    return {'output': result}

# 해결 방법 1: 안전한 컬럼 접근
def run(self, inputs, parameters, ctx: NodeContext):
    df = inputs['data']
    
    # 컬럼 존재 확인
    if 'target_column' not in df.columns:
        raise ValueError(f"필수 컬럼 'target_column'이 없습니다. 사용 가능한 컬럼: {list(df.columns)}")
    
    result = df['target_column']
    return {'output': result}

# 해결 방법 2: 유틸리티 함수 사용
def safe_column_access(df: pd.DataFrame, column: str, default_value=None):
    """안전한 컬럼 접근"""
    if column in df.columns:
        return df[column]
    elif default_value is not None:
        return pd.Series([default_value] * len(df), name=column)
    else:
        available_cols = ", ".join(df.columns[:5])  # 처음 5개만 표시
        raise KeyError(f"컬럼 '{column}'을 찾을 수 없습니다. 사용 가능한 컬럼: {available_cols}")

# 해결 방법 3: 입력 검증 강화
def validate(self, inputs, parameters):
    df = inputs.get('data')
    if df is None:
        raise ValueError("입력 데이터가 없습니다")
    
    required_columns = ['id', 'name', 'value']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"필수 컬럼이 누락되었습니다: {missing_columns}\n"
            f"제공된 컬럼: {list(df.columns)}"
        )
```

---

### Q4: 모델 직렬화가 실패해요

**문제**: ML 모델 저장/로드 시 pickle 에러 발생

**해결 방법**:

```python
# 문제가 되는 코드
def run(self, inputs, parameters, ctx: NodeContext):
    model = inputs['trained_model']  # pickle 에러 가능
    predictions = model.predict(inputs['test_data'])
    return {'predictions': predictions}

# 해결 방법 1: 모델 타입별 처리
class ModelHandler:
    @staticmethod
    def save_model(model, model_type: str = None):
        if model_type is None:
            model_type = ModelHandler.detect_model_type(model)
        
        if model_type == 'sklearn':
            return joblib.dumps(model)
        elif model_type == 'pytorch':
            buffer = io.BytesIO()
            torch.save(model.state_dict(), buffer)
            return buffer.getvalue()
        elif model_type == 'tensorflow':
            # TensorFlow 모델 저장
            return model.to_json()
        else:
            # 일반 pickle
            return pickle.dumps(model, protocol=pickle.HIGHEST_PROTOCOL)
    
    @staticmethod
    def detect_model_type(model):
        module = model.__class__.__module__
        if 'sklearn' in module:
            return 'sklearn'
        elif 'torch' in module:
            return 'pytorch'
        elif 'tensorflow' in module:
            return 'tensorflow'
        return 'generic'

# 해결 방법 2: 에러 핸들링 강화
def execute(self, inputs, parameters):
    try:
        model = inputs['trained_model']
        test_data = inputs['test_data']
        
        # 모델 유효성 검증
        if not hasattr(model, 'predict'):
            raise ValueError("유효하지 않은 모델입니다. predict 메서드가 없습니다.")
        
        predictions = model.predict(test_data)
        
    except Exception as e:
        error_msg = f"모델 예측 실패: {str(e)}"
        logger.error(error_msg)
        
        # 상세한 에러 정보 제공
        model_info = {
            'model_type': type(inputs.get('trained_model', None)),
            'test_data_shape': inputs.get('test_data', pd.DataFrame()).shape,
            'error_type': type(e).__name__
        }
        
        raise ValueError(f"{error_msg}\n모델 정보: {model_info}")
    
    return {'predictions': predictions}
```

---

### Q5: 한글 인코딩 문제가 있어요

**문제**: 한글 텍스트 처리 시 인코딩 에러 발생

**해결 방법**:

```python
# 해결 방법 1: 안전한 텍스트 처리
def safe_text_processing(text_data):
    """안전한 텍스트 처리"""
    
    if isinstance(text_data, bytes):
        # bytes를 문자열로 변환
        try:
            text_data = text_data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text_data = text_data.decode('cp949')  # Windows 인코딩
            except UnicodeDecodeError:
                text_data = text_data.decode('utf-8', errors='ignore')
    
    # 텍스트 정규화
    import unicodedata
    text_data = unicodedata.normalize('NFC', text_data)
    
    return text_data

# 해결 방법 2: DataFrame 인코딩 처리
def fix_dataframe_encoding(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame 인코딩 문제 수정"""
    
    result_df = df.copy()
    
    for col in result_df.select_dtypes(include=['object']).columns:
        if result_df[col].dtype == 'object':
            # 문자열 컬럼 인코딩 수정
            result_df[col] = result_df[col].astype(str).apply(
                lambda x: safe_text_processing(x) if pd.notna(x) else x
            )
    
    return result_df

# 사용 예시
class TextProcessingNode(CustomNode):
    def execute(self, inputs, parameters):
        df = inputs['text_data']
        
        # 인코딩 문제 수정
        df = fix_dataframe_encoding(df)
        
        # 텍스트 처리
        df['processed_text'] = df['text_column'].apply(
            lambda x: self.process_korean_text(x)
        )
        
        return {'processed_data': df}
    
    def process_korean_text(self, text: str) -> str:
        """한글 텍스트 처리"""
        if pd.isna(text):
            return ""
        
        # 한글 정규화
        text = safe_text_processing(text)
        
        # 추가 처리 로직...
        
        return text
```

---

## 🛠️ 성능 최적화 팁

### 메모리 사용량 최적화

```python
# 메모리 사용량 모니터링
import psutil
import os

def get_memory_usage():
    """현재 메모리 사용량 반환 (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

class MemoryOptimizedNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        start_memory = get_memory_usage()
        logger.info(f"시작 메모리: {start_memory:.1f}MB")
        
        # 처리 로직
        result = self.process_data(inputs['data'])
        
        end_memory = get_memory_usage()
        logger.info(f"종료 메모리: {end_memory:.1f}MB (증가: {end_memory-start_memory:.1f}MB)")
        
        return result
    
    def process_data(self, df: pd.DataFrame):
        # 데이터 타입 최적화
        df = self.optimize_dtypes(df)
        
        # 불필요한 컬럼 제거
        df = df.drop(columns=['unnecessary_col1', 'unnecessary_col2'], errors='ignore')
        
        # 중복 제거
        df = df.drop_duplicates()
        
        return df
    
    def optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 타입 최적화로 메모리 절약"""
        
        for col in df.columns:
            if df[col].dtype == 'int64':
                # int32로 다운캐스팅 가능한지 확인
                if df[col].min() >= -2147483648 and df[col].max() <= 2147483647:
                    df[col] = df[col].astype('int32')
            
            elif df[col].dtype == 'float64':
                # float32로 다운캐스팅
                df[col] = pd.to_numeric(df[col], downcast='float')
            
            elif df[col].dtype == 'object':
                # 카테고리로 변환 (반복값이 많은 경우)
                if df[col].nunique() / len(df) < 0.5:
                    df[col] = df[col].astype('category')
        
        return df
```

### 실행 속도 최적화

```python
# 벡터화 연산 활용
class FastNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        df = inputs['data']
        
        # 느린 방법: apply 사용
        # df['result'] = df.apply(lambda x: x['a'] * x['b'], axis=1)
        
        # 빠른 방법: 벡터화 연산
        df['result'] = df['a'] * df['b']
        
        # 느린 방법: 반복문
        # results = []
        # for idx, row in df.iterrows():
        #     results.append(row['a'] + row['b'])
        
        # 빠른 방법: 벡터 연산
        df['sum'] = df['a'] + df['b']
        
        return {'processed_data': df}
```

---

## 🔍 디버깅 가이드

### 로깅 설정

```python
import logging

class DebuggableNode(CustomNode):
    def __init__(self):
        super().__init__()
        self.setup_logging()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('node_debug.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self, inputs, parameters, ctx: NodeContext):
        self.logger.info("노드 실행 시작")
        self.logger.debug(f"입력 데이터 크기: {len(inputs.get('data', []))}")
        self.logger.debug(f"파라미터: {parameters}")
        
        try:
            result = self.process_data(inputs, parameters)
            self.logger.info("노드 실행 성공")
            return result
            
        except Exception as e:
            self.logger.error(f"노드 실행 실패: {str(e)}", exc_info=True)
            raise
    
    def process_data(self, inputs, parameters):
        # 중간 결과 로깅
        intermediate_result = inputs['data'].head()
        self.logger.debug(f"중간 결과 미리보기:\n{intermediate_result}")
        
        # 실제 처리...
        return {'processed_data': inputs['data']}
```

### 데이터 검증 체크리스트

```python
def comprehensive_data_validation(df: pd.DataFrame, node_name: str = "Unknown"):
    """종합적인 데이터 검증"""
    
    validation_results = {
        'node_name': node_name,
        'timestamp': datetime.now().isoformat(),
        'data_shape': df.shape,
        'issues': []
    }
    
    # 1. 기본 정보 확인
    if df.empty:
        validation_results['issues'].append("데이터가 비어있음")
        return validation_results
    
    # 2. 결측값 확인
    null_counts = df.isnull().sum()
    high_null_cols = null_counts[null_counts > len(df) * 0.5].index.tolist()
    if high_null_cols:
        validation_results['issues'].append(f"50% 이상 결측값 컬럼: {high_null_cols}")
    
    # 3. 데이터 타입 확인
    object_cols = df.select_dtypes(include=['object']).columns
    for col in object_cols:
        try:
            pd.to_numeric(df[col])
            validation_results['issues'].append(f"'{col}' 컬럼이 숫자로 변환 가능하지만 object 타입임")
        except:
            pass
    
    # 4. 중복값 확인
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        validation_results['issues'].append(f"중복 행 {duplicate_count}개 발견")
    
    # 5. 메모리 사용량 확인
    memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
    validation_results['memory_usage_mb'] = round(memory_mb, 2)
    if memory_mb > 100:
        validation_results['issues'].append(f"높은 메모리 사용량: {memory_mb:.1f}MB")
    
    return validation_results

# 사용 예시
class ValidatedNode(CustomNode):
    def run(self, inputs, parameters, ctx: NodeContext):
        df = inputs['data']
        
        # 입력 데이터 검증
        validation_result = comprehensive_data_validation(df, self.__class__.__name__)
        
        if validation_result['issues']:
            logger.warning(f"데이터 품질 이슈: {validation_result['issues']}")
            # 심각한 이슈가 있으면 실행 중단
            critical_issues = [issue for issue in validation_result['issues'] 
                             if '비어있음' in issue or '필수' in issue]
            if critical_issues:
                raise ValueError(f"심각한 데이터 이슈: {critical_issues}")
        
        # 처리 로직...
        result = self.process_data(df)
        
        return {'processed_data': result, 'validation_info': validation_result}
```

---

## 추가 지원

### 문제 해결이 어려운 경우

1. **로그 파일 확인**: `~/.aicanvas/sdk.log`
2. **샘플 데이터로 테스트**: `aicanvas-sdk test your_node.py --sample-data`
3. **디버그 모드 실행**: `aicanvas-sdk test your_node.py --debug`
4. **메모리 프로파일링**: `aicanvas-sdk profile your_node.py`

### 지원 채널

- **기술 지원**: tech-support@aicanvas.com
- **버그 리포트**: GitHub Issues
- **기능 요청**: feature-request@aicanvas.com
- **커뮤니티**: AI Canvas Developer Forum

### 자주 사용하는 디버깅 명령어

```bash
# 노드 스키마 검증
aicanvas-sdk validate my_node.py

# 샘플 데이터로 테스트
aicanvas-sdk test my_node.py --sample-data --verbose

# 성능 프로파일링
aicanvas-sdk profile my_node.py --iterations 10

# 메모리 사용량 모니터링
aicanvas-sdk monitor my_node.py --memory

# 에러 로그 실시간 확인
tail -f ~/.aicanvas/sdk.log
```

---

**추가 질문이나 문제가 있으시면 언제든 문의해 주세요!**