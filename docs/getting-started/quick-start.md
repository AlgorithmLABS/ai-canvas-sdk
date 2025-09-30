# 빠른 시작 가이드

5분 만에 첫 번째 AI Canvas 커스텀 노드를 만들고 실행해보세요.

## 목표

이 가이드를 완료하면:
- 간단한 텍스트 처리 노드 생성
- 로컬에서 노드 테스트
- AI Canvas 플랫폼에 노드 등록

## 전제 조건

- [설치 가이드](./installation.md)에 따라 SDK 설치 완료
- Python 3.10+ 환경

## Step 1: 첫 번째 노드 생성

`hello_node.py` 파일을 생성합니다:

```python
from ai_canvas_sdk import CustomNode, NodeSchema, PortType, NodeContext

class HelloWorldNode(CustomNode):
    """간단한 텍스트 처리 노드"""
    
    @staticmethod
    def get_schema() -> NodeSchema:
        return NodeSchema(
            name="HelloWorld",
            display_name="Hello World 노드",
            description="입력 텍스트에 인사말을 추가합니다",
            category="text_processing",
            inputs=[

            ],
            outputs=[
                {
                    "name": "output_text", 
                    "display_name": "출력 텍스트",
                    "type": PortType.DATASET
                }
            ],
            parameters=[
                {
                    "name": "greeting",
                    "display_name": "인사말",
                    "type": "text",
                    "default": "Hello",
                    "description": "앞에 붙일 인사말을 입력하세요"
                },
                {
                    "name":"user_name",
                    "display_name":"이름",
                    "type":"text",
                    "default":"Hong",
                    "description":"사용자 이름을 입력하세요"
                }
            ]
        )
    
    def run(self, parameters: dict, ctx: NodeContext) -> dict:
        """노드 실행 로직"""
        # 입력 데이터 받기
        user_name = parameters.get('user_name', 'Hong')
        greeting = parameters.get('greeting', 'Hello')
        
        # 비즈니스 로직
        # 비즈니스 로직
        # 'pd'와 'Dataset'을 import해야 합니다.
        # 예: import pandas as pd
        # 예: from ai_canvas_sdk.types import Dataset
        df=pd.DataFrame({
            "name":[user_name],
            "greeting":[f"{greeting} {user_name}"]
        })
        
        # 결과 반환
        return {"output_text": Dataset(dataframe=df)}

node = HelloWorldNode()
```


## Step 2: 데이터프레임 노드 예제

DataFrame 처리 노드를 만들어보겠습니다:

`data_filter_node.py`:

```python
from ai_canvas_sdk import CustomNode, NodeSchema, PortType, NodeContext
import pandas as pd

class DataFilterNode(CustomNode):
    """데이터 필터링 노드"""
    
    @staticmethod
    def get_schema() -> NodeSchema:
        return NodeSchema(
            name="DataFilter",
            display_name="데이터 필터",
            description="조건에 맞는 데이터만 필터링합니다",
            category="data_processing",
            inputs=[
                {
                    "name": "input_data",
                    "display_name": "입력 데이터",
                    "type": PortType.DATASET,
                    "required": True
                }
            ],
            outputs=[
                {
                    "name": "filtered_data",
                    "display_name": "필터링된 데이터",
                    "type": PortType.DATASET
                },
                {
                    "name": "stats",
                    "display_name": "필터링 통계",
                    "type": PortType.DISPLAY
                }
            ],
            parameters=[
                {
                    "name": "column",
                    "display_name": "필터 컬럼",
                    "type": "text",
                    "required": True,
                    "description": "필터링할 컬럼명"
                },
                {
                    "name": "threshold",
                    "display_name": "임계값",
                    "type": "number",
                    "default": 0,
                    "description": "이 값보다 큰 데이터만 유지"
                }
            ]
        )
    
    def validate(self, inputs: Dataset, parameters: dict) -> None:
        """입력 검증"""
        df = inputs.dataframe
        column = parameters.get('column')
        
        if df is None or df.empty:
            raise ValueError("입력 데이터가 비어있습니다")
        
        if column not in df.columns:
            raise ValueError(f"컬럼 '{column}'이 데이터에 존재하지 않습니다")
    
    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs['input_data']
        column = parameters['column']
        threshold = parameters.get('threshold', 0)
        
        # 데이터 필터링
        filtered_df = df[df[column] > threshold]
        
        # 통계 생성
        stats = {
            "original_rows": len(df),
            "filtered_rows": len(filtered_df),
            "filter_ratio": len(filtered_df) / len(df) if len(df) > 0 else 0,
            "column": column,
            "threshold": threshold
        }
        
        return (Dataset(dataframe=filtered_df),Display(stats))

node = DataFilterNode()
```

### 데이터프레임 테스트

```bash
# 샘플 데이터로 테스트
ai-canvas-sdk test data_filter_node.py --sample-data
```

SDK가 자동으로 샘플 DataFrame을 생성해서 테스트합니다.

## Step 3: 서버에 노드 등록

### 3.1 노드 패키징

```bash
# 노드 패키지 생성
ai-canvas-sdk package \
  --nodes data_filter_node.py \
  --output my_custom_nodes.zip \
  --version "1.0.0"
```

### 3.2 서버 등록

```bash
# 서버에 노드 등록
ai-canvas-sdk register \
  --package my_custom_nodes.zip \
  --server https://your-aicanvas-custom-node-server.com \
  --api-key YOUR_API_KEY
```

성공하면 다음과 같은 메시지가 표시됩니다:
```
노드 등록 완료!
노드 ID: hello-world-v1.0.0, data-filter-v1.0.0
서버: https://your-aicanvas-custom-node-server.com
```

## Step 4: AI Canvas에서 사용

1. **AI Canvas 웹 인터페이스 접속**
2. **새 캔버스 생성**
3. **노드 팔레트에서 "Custom Node" 카테고리 확인**
4. **데이터 필터 노드를 캔버스로 드래그**
5. **노드 설정에서 파라미터 입력**
6. **실행 버튼 클릭**

## 성능 확인

### 실행 시간 측정

```bash
# 성능 프로파일링
ai-canvas-sdk profile hello_node.py \
  --input '{"input_text": "Performance Test"}' \
  --iterations 100
```

결과 예시:
```
성능 보고서
평균 실행 시간: 2.3ms
메모리 사용량: 1.2MB
직렬화 오버헤드: 0.8ms
네트워크 지연: 15ms
```

### 대용량 데이터 테스트

```python
# large_data_test.py
import pandas as pd
from ai_canvas_sdk.testing import create_sample_dataframe

# 10만 행 데이터 생성
large_df = create_sample_dataframe(rows=100000, columns=10)

# 노드 테스트
ctx = NodeContext()
result = data_filter_node.run(
    inputs={'input_data': large_df},
    parameters={'column': 'value', 'threshold': 0.5},
    ctx=ctx,
)

print(f"처리된 행 수: {len(result['filtered_data'])}")
print(f"통계: {result['stats']}")
```

## 완료!

축하합니다! 첫 번째 AI Canvas 커스텀 노드를 성공적으로 만들고 실행했습니다.


### 학습 팁

- **작게 시작**: 간단한 기능부터 구현
- **자주 테스트**: `ai-canvas-sdk test` 명령을 활용
- **로그 확인**: `~/.ai-canvas/sdk.log` 파일 모니터링
