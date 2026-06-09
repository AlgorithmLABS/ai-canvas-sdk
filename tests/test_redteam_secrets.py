"""Red-team(적대적) black-box 검증: SDK 공개 표면(secret 소비 + proto).

surface=package/api. 공개 API만 사용해 secret 격리/비노출, mutable default,
proto round-trip 계약을 깨려 시도한다.
"""

import pytest

# 공개 표면은 top-level import 로만 접근 (black-box)
from ai_canvas_sdk import (
    CustomNode,
    NodeContext,
    SecretNotAvailableError,
    CustomNodeError,
)
from ai_canvas_sdk.grpc import custom_node_service_pb2 as pb2


def _ctx(secrets=None):
    return NodeContext(execution_id="exec-1", node_id="node-1", secrets=secrets)


# ---------------------------------------------------------------------------
# 1) get_secret 경계/적대 입력
#    contractRef: ctx.get_secret(name)->str, 선언된 것만 반환, 미존재→SecretNotAvailableError
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "",  # 빈 문자열
        "does-not-exist",  # 존재하지 않는 이름
        "날씨-키",  # 유니코드 이름
        "🔑",  # 이모지 이름
        "get",  # dict 메서드명
        "items",
        "keys",
        "values",
        "__class__",  # dunder 속성명
        "__dict__",
        "pop",
        "update",
    ],
)
def test_get_secret_adversarial_names_raise_when_not_injected(name):
    """주입되지 않은 임의/적대 이름은 dict 내부 메서드명이라도 예외만 발생."""
    ctx = _ctx({"weather-api": "k-123"})
    with pytest.raises(SecretNotAvailableError):
        ctx.get_secret(name)


@pytest.mark.parametrize(
    "name,value",
    [
        ("", "empty-name-value"),
        ("날씨-키", "유니코드-값"),
        ("🔑", "emoji-value"),
        ("get", "method-name-value"),  # dict 메서드명도 secret 이름으로 정상 동작
        ("__class__", "dunder-value"),
    ],
)
def test_get_secret_adversarial_names_returned_when_injected(name, value):
    """적대적 이름이라도 실제 주입되면 정확히 그 값만 반환(이름은 평범한 dict key)."""
    ctx = _ctx({name: value})
    assert ctx.get_secret(name) == value


def test_get_secret_does_not_fall_back_to_dict_methods():
    """'get' 등의 이름이 dict.get 메서드 객체로 새지 않음을 확인."""
    ctx = _ctx({"real": "v"})
    with pytest.raises(SecretNotAvailableError):
        ctx.get_secret("get")


# ---------------------------------------------------------------------------
# 2) 값 격리: 한 secret 조회 실패가 다른 secret 값을 노출하지 않음
#    contractRef: SecretNotAvailableError 메시지에 다른 secret 값 미포함
# ---------------------------------------------------------------------------


def test_other_secret_values_never_leak_in_error():
    secrets = {
        "alpha": "AAAA-very-secret",
        "beta": "BBBB-also-secret",
        "gamma": "GGGG-top-secret",
    }
    ctx = _ctx(secrets)
    with pytest.raises(SecretNotAvailableError) as exc:
        ctx.get_secret("missing")
    msg = str(exc.value)
    rendered = repr(exc.value) + "|" + msg
    for v in secrets.values():
        assert v not in rendered, f"secret 값 누출: {v!r}"
    # 조회한 이름은 메시지에 있어도 무방, 값은 절대 없음
    assert "missing" in msg


def test_failed_lookup_of_existing_other_does_not_leak():
    """존재하는 다른 secret 이 있어도 실패 메시지에 그 값이 없음."""
    ctx = _ctx({"present": "PRESENT-SECRET-VALUE"})
    with pytest.raises(SecretNotAvailableError) as exc:
        ctx.get_secret("absent")
    assert "PRESENT-SECRET-VALUE" not in str(exc.value)
    assert "PRESENT-SECRET-VALUE" not in repr(exc.value)


# ---------------------------------------------------------------------------
# 3) 전체 dict 비노출 + 방어적 복사 동작 확인
#    contractRef: secrets 전체를 반환하는 공개 속성/메서드 없음(get_secret만 공개)
# ---------------------------------------------------------------------------


def test_no_public_attribute_exposes_full_secrets_dict():
    secrets = {"alpha": "AAAA", "beta": "BBBB"}
    ctx = _ctx(secrets)
    public_names = [n for n in dir(ctx) if not n.startswith("_")]
    # 어떤 public 속성/메서드도 전체 secrets dict 를 반환하지 않아야 함
    for name in public_names:
        attr = getattr(ctx, name)
        if callable(attr):
            continue  # get_secret 등 호출형은 인자 없이 dict 전체 못 얻음
        # 비호출형 속성 값이 secrets dict 와 동일하면 누출
        assert attr is not secrets
        assert attr != secrets
    # secrets 라는 이름의 public 표면이 아예 없어야 함
    assert "secrets" not in public_names
    assert "get_secrets" not in public_names


def test_get_secret_is_the_only_public_secret_surface():
    ctx = _ctx({"a": "1"})
    public_names = {n for n in dir(ctx) if not n.startswith("_")}
    secretish = {n for n in public_names if "secret" in n.lower()}
    assert secretish == {"get_secret"}


def test_injected_secrets_dict_is_defensively_copied():
    """주입 dict 를 외부에서 변경해도 ctx 상태가 오염되지 않아야 한다.

    NodeContext 는 `dict(secrets or {})` 로 방어적 복사를 하므로, 생성 이후
    호출자의 원본 dict 변경이 ctx.get_secret 결과에 반영되지 않는다.
    """
    external = {"a": "1"}
    ctx = _ctx(external)
    # 외부에서 secret 추가/변경
    external["b"] = "2"
    external["a"] = "MUT"
    # 방어적 복사이므로 ctx 는 생성 시점 스냅샷을 유지한다
    with pytest.raises(SecretNotAvailableError):
        ctx.get_secret("b")
    assert ctx.get_secret("a") == "1"


def test_none_secrets_isolated_between_contexts():
    """secrets=None 두 컨텍스트가 동일한 내부 dict 를 공유하지 않음."""
    c1 = _ctx()
    c2 = _ctx()
    c1._secrets["x"] = "leak"  # 내부 직접 변경(white-box 보조 확인)
    with pytest.raises(SecretNotAvailableError):
        c2.get_secret("x")


# ---------------------------------------------------------------------------
# 4) mutable default 처리: 서브클래스 override 간섭 없음, base 는 [] 유지
#    contractRef: CustomNode.required_secrets: list[str] = [], 서브클래스 override
# ---------------------------------------------------------------------------


def test_base_custom_node_required_secrets_is_empty():
    assert CustomNode.required_secrets == []


def test_subclass_override_no_cross_contamination():
    class NodeA(CustomNode):
        required_secrets = ["alpha-key"]

        def get_schema(self):  # pragma: no cover - 추상 충족용
            raise NotImplementedError

        def execute(self, *a, **k):  # pragma: no cover
            raise NotImplementedError

    class NodeB(CustomNode):
        required_secrets = ["beta-key", "gamma-key"]

        def get_schema(self):  # pragma: no cover
            raise NotImplementedError

        def execute(self, *a, **k):  # pragma: no cover
            raise NotImplementedError

    assert NodeA.required_secrets == ["alpha-key"]
    assert NodeB.required_secrets == ["beta-key", "gamma-key"]
    # 서로 간섭 없음
    assert NodeA.required_secrets != NodeB.required_secrets
    # base 는 여전히 비어 있음 (공유 기본값 오염 없음)
    assert CustomNode.required_secrets == []


def test_subclass_inplace_mutation_does_not_touch_base():
    """서브클래스가 자신의 리스트를 in-place 변경해도 base [] 불변."""
    class NodeC(CustomNode):
        required_secrets = ["c1"]

        def get_schema(self):  # pragma: no cover
            raise NotImplementedError

        def execute(self, *a, **k):  # pragma: no cover
            raise NotImplementedError

    NodeC.required_secrets.append("c2")
    assert NodeC.required_secrets == ["c1", "c2"]
    assert CustomNode.required_secrets == []


# ---------------------------------------------------------------------------
# 5) proto round-trip
#    contractRef: NodeDefinition.required_secrets 필드 11 repeated string (additive)
# ---------------------------------------------------------------------------


def test_proto_field_metadata():
    field = pb2.NodeDefinition.DESCRIPTOR.fields_by_name["required_secrets"]
    assert field.number == 11
    assert field.label == field.LABEL_REPEATED
    assert field.type == field.TYPE_STRING


def test_proto_roundtrip_preserves_required_secrets():
    nd = pb2.NodeDefinition(
        name="n",
        required_secrets=["weather-api", "db-pass"],
    )
    blob = nd.SerializeToString()
    restored = pb2.NodeDefinition()
    restored.ParseFromString(blob)
    assert list(restored.required_secrets) == ["weather-api", "db-pass"]


def test_proto_required_secrets_defaults_empty():
    nd = pb2.NodeDefinition(name="n")
    assert list(nd.required_secrets) == []
    restored = pb2.NodeDefinition()
    restored.ParseFromString(nd.SerializeToString())
    assert list(restored.required_secrets) == []


def test_proto_roundtrip_large_required_secrets():
    names = [f"secret-{i}" for i in range(100)]
    nd = pb2.NodeDefinition(name="n", required_secrets=names)
    restored = pb2.NodeDefinition()
    restored.ParseFromString(nd.SerializeToString())
    assert list(restored.required_secrets) == names
    assert len(restored.required_secrets) == 100


def test_proto_required_secrets_coexists_with_existing_fields():
    nd = pb2.NodeDefinition(
        name="my-node",
        category="utils",
        version="1.0.0",
        dependencies=["numpy", "pandas"],
        required_secrets=["api-key"],
    )
    restored = pb2.NodeDefinition()
    restored.ParseFromString(nd.SerializeToString())
    assert restored.name == "my-node"
    assert restored.category == "utils"
    assert restored.version == "1.0.0"
    assert list(restored.dependencies) == ["numpy", "pandas"]
    assert list(restored.required_secrets) == ["api-key"]


def test_proto_unicode_required_secrets_roundtrip():
    names = ["날씨-키", "🔑", "café-token"]
    nd = pb2.NodeDefinition(name="n", required_secrets=names)
    restored = pb2.NodeDefinition()
    restored.ParseFromString(nd.SerializeToString())
    assert list(restored.required_secrets) == names
