"""proto NodeDefinition.required_secrets 필드 회귀 방지 테스트."""

from ai_canvas_sdk.grpc import custom_node_service_pb2 as pb


def test_node_definition_has_required_secrets_field():
    fields = pb.NodeDefinition.DESCRIPTOR.fields_by_name
    assert "required_secrets" in fields


def test_required_secrets_is_field_11_repeated_string():
    field = pb.NodeDefinition.DESCRIPTOR.fields_by_name["required_secrets"]
    assert field.number == 11
    assert field.is_repeated
    assert field.cpp_type == field.CPPTYPE_STRING


def test_required_secrets_defaults_empty():
    node = pb.NodeDefinition(name="n", required_secrets=["weather-api"])
    assert list(node.required_secrets) == ["weather-api"]
    empty = pb.NodeDefinition(name="n2")
    assert list(empty.required_secrets) == []
