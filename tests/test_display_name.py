"""Registration metadata contract for custom-node display names."""

from __future__ import annotations

import pytest

from ai_canvas_sdk.custom_node.models.node_schema import NodeData, NodeMetadata, NodeSchema


def make_schema(
    display_name: dict[str, str] | None = None,
    *,
    metadata: NodeMetadata | None = None,
) -> NodeSchema:
    return NodeSchema(
        name="sales_forecast",
        data=NodeData(input_ports=[], output_ports=[]),
        display_name=display_name,
        metadata=metadata,
    )


def test_display_name_serializes_to_registration_custom_metadata() -> None:
    schema = make_schema({"ko": "매출 예측", "en": "Sales Forecast"})

    assert schema.metadata is not None
    assert schema.metadata.custom_metadata["display_name"] == (
        '{"ko": "매출 예측", "en": "Sales Forecast"}'
    )
    assert "\\u" not in schema.metadata.custom_metadata["display_name"]


@pytest.mark.parametrize("display_name", [None])
def test_display_name_none_does_not_add_registration_metadata(
    display_name: dict[str, str] | None,
) -> None:
    metadata = NodeMetadata(custom_metadata={"owner": "forecasting"})

    schema = make_schema(display_name, metadata=metadata)

    assert schema.metadata is metadata
    assert schema.metadata.custom_metadata == {"owner": "forecasting"}
    assert "display_name" not in schema.metadata.custom_metadata


def test_display_name_unset_does_not_create_metadata() -> None:
    schema = NodeSchema(
        name="sales_forecast",
        data=NodeData(input_ports=[], output_ports=[]),
    )

    assert schema.metadata is None


def test_empty_display_name_is_serialized_as_declared_value() -> None:
    schema = make_schema({})

    assert schema.metadata is not None
    assert schema.metadata.custom_metadata["display_name"] == "{}"


@pytest.mark.parametrize(
    "display_name",
    [
        pytest.param({"ko": 1}, id="number"),
        pytest.param({"ko": {"x": 1}}, id="nested-dict"),
    ],
)
def test_display_name_rejects_non_string_values_at_serialization(
    display_name: dict[str, object],
) -> None:
    with pytest.raises(TypeError, match=r"display_name\['ko'\] must be str"):
        make_schema(display_name)  # type: ignore[arg-type]


def test_display_name_rejects_unknown_locale() -> None:
    with pytest.raises(ValueError, match=r"unsupported display_name locale 'fr'"):
        make_schema({"fr": "x"})
