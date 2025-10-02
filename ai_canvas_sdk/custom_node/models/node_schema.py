from dataclasses import dataclass, field
from datetime import datetime

from ai_canvas_sdk.custom_node.models.parameter import Parameter
from ai_canvas_sdk.custom_node.models.port import Port


@dataclass
class NodeData:
    input_ports: list[Port]
    output_ports: list[Port]
    params: list[Parameter] = field(default_factory=list)


@dataclass
class NodeMetadata:
    author: str = ""
    license: str = ""
    documentation_url: str = ""
    source_code_url: str = ""
    custom_metadata: dict = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class NodeSchema:
    name: str
    data: NodeData
    category: str = "custom"
    width: int = 200
    height: int = 142
    version: str = "1.0.0"
    metadata: NodeMetadata | None = None
    source_code: str = ""
    entry_class: str = ""
    dependencies: list[str] = field(default_factory=list)
