"""공공 OpenAPI 조회 노드 예제 (secret 으로 API 키 주입)

공공데이터포털(data.go.kr) OpenAPI 에서 데이터를 조회해 DataFrame 으로 반환하는
커스텀 노드 예제입니다. API 인증키(serviceKey)를 코드에 하드코딩하지 않고
`required_secrets` + `ctx.get_secret()` 으로 안전하게 주입받는 방법을 보여줍니다.

핵심 포인트
- `required_secrets = ["public_data_api_key"]` : 클래스 속성 리터럴로 선언(등록 시 AST 정적 추출).
- 값은 노드 코드가 아니라 관리자가 Secret Store 에 등록하고, 실행 시 `ctx.get_secret()` 으로만 꺼낸다.
- `dependencies=["requests"]` : 외부 패키지를 스키마에 선언. `import requests` 는 실행 시점 지연 import.
- secret 값은 로그·출력 포트 어디에도 노출하지 않는다(로그에는 건수 등 메타데이터만).

주의: 응답 파싱(`response.body.items.item`)은 data.go.kr 공통 JSON 응답 구조를 가정한 것으로,
      실제 엔드포인트 규격에 맞춰 조정이 필요할 수 있습니다.

로컬 테스트:
    ai-canvas-sdk test public-data-node.py --validate-only
    ai-canvas-sdk test public-data-node.py -s "public_data_api_key=$DATA_GO_KR_KEY"
"""

import pandas as pd
from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    NodeData,
    NodeSchema,
    Parameter,
    Port,
    PortEnum,
    PortTypeEnum,
    PositionEnum,
)


class PublicDataNode(CustomNode):
    """공공데이터포털(data.go.kr) OpenAPI 에서 데이터를 조회해 DataFrame 으로 반환하는 노드."""

    # 실행 시 플랫폼이 주입할 secret 이름. 값은 관리자가 Secret Store 에 등록한다.
    required_secrets = ["public_data_api_key"]

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="PublicDataFetch",
            data=NodeData(
                input_ports=[],  # 외부 API 에서 가져오므로 입력 포트가 없다
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="data",
                    ),
                ],
                params=[
                    Parameter(
                        text="엔드포인트 URL",
                        name="endpoint",
                        form_type="input",
                        value="https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst",
                        value_type="string",
                        is_tab=True,
                    ),
                    Parameter(
                        text="조회 행 수",
                        name="num_of_rows",
                        form_type="number",
                        value=100,
                        value_type="number",
                        is_tab=True,
                    ),
                ],
            ),
            version="1.0.0",
            dependencies=["requests"],  # 이 노드가 필요로 하는 외부 패키지
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        import requests  # 선택적/무거운 의존성은 실행 시점에 지연 import

        # 1) secret 조회 — 값은 로그·출력 어디에도 노출하지 않는다
        api_key = ctx.get_secret("public_data_api_key")

        endpoint = parameters.get("endpoint")
        num_of_rows = int(parameters.get("num_of_rows", 100))

        ctx.log_info(f"공공 API 호출: {endpoint} (numOfRows={num_of_rows})")  # 키는 로그에 남기지 않음
        ctx.progress(0.2)

        # 2) serviceKey 로 인증(data.go.kr 규격), _type=json 으로 JSON 응답 요청
        resp = requests.get(
            endpoint,
            params={
                "serviceKey": api_key,
                "numOfRows": num_of_rows,
                "pageNo": 1,
                "_type": "json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        ctx.progress(0.6)

        # 3) 공통 응답 구조에서 items 추출 → DataFrame
        items = resp.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(items, dict):  # 단건이면 dict, 다건이면 list 로 온다
            items = [items]
        df = pd.DataFrame(items)

        ctx.log_info(f"{len(df)}건 수신")  # 건수만 로그
        ctx.progress(1.0)
        return {"data": df}


# 노드 인스턴스 생성 (SDK 가 이 인스턴스를 찾는다)
node = PublicDataNode()
