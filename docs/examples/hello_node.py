"""CLI 로컬 테스트용 Hello World 노드."""

from __future__ import annotations

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


class HelloWorldNode(CustomNode):
    """입력 DataFrame에 인사말 컬럼을 붙입니다."""

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="HelloWorld",
            category="custom",
            version="1.0.0",
            data=NodeData(
                input_ports=[
                    Port(
                        type=PortEnum.TARGET,
                        position=PositionEnum.LEFT,
                        port_type=PortTypeEnum.DATASET,
                        label="input_data",
                    ),
                ],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="output_data",
                    ),
                ],
                params=[
                    Parameter(
                        text="인사말",
                        name="greeting",
                        form_type="input",
                        value="Hello",
                    ),
                ],
            ),
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        df = inputs.get("input_data")
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("input_data 포트에 DataFrame이 필요합니다")

        greeting = parameters.get("greeting", "Hello")
        ctx.log_info(f"processing {len(df)} rows")
        ctx.progress(0.5)

        result = df.copy()
        if "name" in result.columns:
            result["greeting"] = result["name"].map(lambda name: f"{greeting} {name}")
        else:
            result["greeting"] = greeting

        ctx.progress(1.0)
        return {"output_data": result}
