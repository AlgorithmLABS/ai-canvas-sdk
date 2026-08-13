import json
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
    display_name: dict[str, str] | None = None

    def __post_init__(self) -> None:
        self.serialize_metadata()

    def serialize_metadata(self) -> NodeMetadata | None:
        """Serialize SDK-only declarations into registration wire metadata.

        ``display_name`` currently supports the ``ko`` and ``en`` wire locales.
        An empty mapping is a declared value and is therefore serialized as ``{}``.
        """
        if self.display_name is None:
            return self.metadata
        if not isinstance(self.display_name, dict):
            raise TypeError("display_name must be a dict[str, str] or None")

        supported_locales = {"ko", "en"}
        for locale, value in self.display_name.items():
            if not isinstance(locale, str):
                raise TypeError("display_name locale keys must be str")
            if locale not in supported_locales:
                raise ValueError(f"unsupported display_name locale {locale!r}; expected 'ko' or 'en'")
            if not isinstance(value, str):
                raise TypeError(
                    f"display_name[{locale!r}] must be str, got {type(value).__name__}"
                )

        if self.metadata is None:
            self.metadata = NodeMetadata()
        self.metadata.custom_metadata["display_name"] = json.dumps(
            self.display_name,
            ensure_ascii=False,
        )
        return self.metadata
