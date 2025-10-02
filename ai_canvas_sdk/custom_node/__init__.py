from abc import ABC, abstractmethod

from ai_canvas_sdk.custom_node.models.node_schema import NodeData, NodeMetadata, NodeSchema
from ai_canvas_sdk.custom_node.models.parameter import Parameter
from ai_canvas_sdk.custom_node.models.port import Port
from ai_canvas_sdk.custom_node.node_context import NodeContext


class CustomNode(ABC):
    """
    커스텀 노드 기본 클래스
    사용자는 이 클래스를 상속받아 다음 메서드를 구현해야 합니다:
      1. get_schema(): 노드 스키마 정의 (이름, 포트, 파라미터 등)
      2. run(): 노드 실행 로직
      3. validate(): 입력 검증 (선택적)



    """

    @abstractmethod
    def get_schema(self) -> NodeSchema:
        """
        노드 스키마를 반환.

        노드의 이름, 포트, 파라미터, 메타데이터 등을 정의.
        이 정보는 노드 등록 시 backend와 ai_canvas_cne 에 전달됨.

        returns:
            NodeSchema: 노드 스키마
        """
        pass

    @abstractmethod
    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        """
        노드를 실행합니다.

        입력 포트의 데이터와 파라미터를 받아 노드를 실행.

        Args:
            inputs (dict): 입력 포트 데이터
                - value: 데이터 (주로 pandas.DataFrame, 또는 dict, list 등)
                - 예: {"input_data": pd.DataFrame(...)}

            parameters (dict): 파라미터 값
                - key: 파라미터 name (예: "multiplier")
                - value: 파라미터 값 (number, string, boolean 등)
                - 예: {"multiplier": 2.0, "method": "mean"}

              ctx (NodeContext): 실행 컨텍스트
                  - 로그 출력: ctx.log_info("message"), ctx.log_error("error") 등
                  - 진행률 보고: ctx.progress(0.5)  # 0.0 ~ 1.0
                  - 취소 확인: if ctx.is_cancelled(): raise Exception("Cancelled")
                  - 실행 정보: ctx.execution_id, ctx.user_id, ctx.node_id 등

          Returns:
              dict: 출력 포트 데이터
                  - key: 포트 ID (예: "output_data")
                  - value: 결과 데이터 (주로 pandas.DataFrame)
                  - 예: {"output_data": result_df}

          Raises:
              ValueError: 입력 데이터나 파라미터가 잘못된 경우
              Exception: 실행 중 에러 발생 시

          Example:
              ```python
              def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
                  ctx.log_info("Starting processing")

                  # 입력 가져오기
                  df = inputs['input_data']
                  multiplier = parameters.get('multiplier', 1.0)

                  # 취소 확인
                  if ctx.is_cancelled():
                      raise Exception("Execution cancelled")

                  # 처리
                  ctx.progress(0.5)
                  result = df * multiplier

                  ctx.progress(1.0)
                  ctx.log_info("Completed")

                  return {'output_data': result}
              ```
        """
        pass


__all__ = [
    "CustomNode",
    "NodeSchema",
    "NodeData",
    "NodeMetadata",
    "NodeContext",
    "Parameter",
    "Port",
]
