"""NodeContext secret 소비 인터페이스 단위 테스트."""

import pytest

from ai_canvas_sdk.custom_node.exceptions import SecretNotAvailableError
from ai_canvas_sdk.custom_node.node_context import NodeContext


def _ctx(secrets=None):
    return NodeContext(execution_id="exec-1", node_id="node-1", secrets=secrets)


def test_get_secret_returns_declared_value():
    ctx = _ctx({"weather-api": "k-123"})
    assert ctx.get_secret("weather-api") == "k-123"


def test_get_secret_missing_raises_secret_not_available():
    ctx = _ctx({"weather-api": "k-123"})
    with pytest.raises(SecretNotAvailableError):
        ctx.get_secret("other-api")


def test_get_secret_default_no_secrets_raises():
    ctx = _ctx()  # secrets 미전달 → 빈 dict
    with pytest.raises(SecretNotAvailableError):
        ctx.get_secret("weather-api")


def test_secret_value_not_in_error_message():
    ctx = _ctx({"weather-api": "super-secret-value"})
    with pytest.raises(SecretNotAvailableError) as exc:
        ctx.get_secret("missing")
    # 미설정 이름은 메시지에 있으나 다른 secret 값은 노출되면 안 됨
    assert "super-secret-value" not in str(exc.value)


def test_secrets_dict_not_publicly_exposed():
    ctx = _ctx({"weather-api": "k-123"})
    # 전체 secrets 를 통째로 노출하는 공개 표면이 없어야 한다 (get_secret 만 공개)
    assert not hasattr(ctx, "secrets")
    public_attrs = [a for a in dir(ctx) if not a.startswith("_")]
    assert "secrets" not in public_attrs
    # 내부 저장은 private 으로만 접근 가능
    assert ctx._secrets == {"weather-api": "k-123"}


def test_secret_not_available_error_is_custom_node_error():
    from ai_canvas_sdk.custom_node.exceptions import CustomNodeError

    assert issubclass(SecretNotAvailableError, CustomNodeError)
