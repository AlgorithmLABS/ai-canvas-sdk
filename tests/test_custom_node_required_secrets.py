"""CustomNode.required_secrets 선언 인터페이스 단위 테스트."""

from ai_canvas_sdk.custom_node import CustomNode


def test_default_required_secrets_is_empty_list():
    assert CustomNode.required_secrets == []


def test_subclass_can_override_required_secrets():
    class WeatherNode(CustomNode):
        required_secrets = ["weather-api"]

        def get_schema(self):  # pragma: no cover - 스키마 본문은 검증 대상 아님
            raise NotImplementedError

        def run(self, inputs, parameters, ctx):  # pragma: no cover
            raise NotImplementedError

    assert WeatherNode.required_secrets == ["weather-api"]
    # 기본값은 변하지 않는다 (override 가 base 를 오염시키지 않음)
    assert CustomNode.required_secrets == []


def test_required_secrets_exported_symbols():
    import ai_canvas_sdk

    assert hasattr(ai_canvas_sdk, "SecretNotAvailableError")
    assert hasattr(ai_canvas_sdk, "CustomNodeError")
