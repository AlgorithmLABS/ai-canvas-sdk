"""CLI test 명령의 --secret 주입 단위/통합 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_canvas_sdk.cli import main
from ai_canvas_sdk.cli.test import _parse_secrets
from ai_canvas_sdk.cli.utils.test_context import create_test_context
from ai_canvas_sdk.custom_node.exceptions import SecretNotAvailableError


# --- _parse_secrets 단위 테스트 ---------------------------------------------

def test_parse_secrets_basic():
    assert _parse_secrets(["api_key=abc", "token=xyz"]) == {"api_key": "abc", "token": "xyz"}


def test_parse_secrets_value_with_equals_preserved():
    # 값에 '=' 가 있어도 첫 '=' 기준으로만 분리 (base64 등)
    assert _parse_secrets(["token=ab=cd=="]) == {"token": "ab=cd=="}


def test_parse_secrets_none_and_empty_return_empty_dict():
    assert _parse_secrets(None) == {}
    assert _parse_secrets([]) == {}


def test_parse_secrets_missing_equals_raises():
    with pytest.raises(ValueError):
        _parse_secrets(["novalue"])


def test_parse_secrets_empty_key_raises():
    with pytest.raises(ValueError):
        _parse_secrets(["=value"])


def test_parse_secrets_empty_value_raises():
    with pytest.raises(ValueError):
        _parse_secrets(["key="])


# --- create_test_context secret 주입 ----------------------------------------

def test_create_test_context_injects_secret():
    ctx = create_test_context(verbose=False, secrets={"api_key": "v-123"})
    assert ctx.get_secret("api_key") == "v-123"


def test_create_test_context_without_secrets_raises():
    ctx = create_test_context(verbose=False)
    with pytest.raises(SecretNotAvailableError):
        ctx.get_secret("api_key")


# --- CLI end-to-end ----------------------------------------------------------

_SECRET_NODE_SOURCE = '''
import pandas as pd
from ai_canvas_sdk import (
    CustomNode, NodeSchema, NodeData, Port,
    PortEnum, PortTypeEnum, PositionEnum, NodeContext,
)


class SecretNode(CustomNode):
    required_secrets = ["api_key"]

    def get_schema(self) -> NodeSchema:
        return NodeSchema(
            name="SecretNode",
            data=NodeData(
                input_ports=[],
                output_ports=[
                    Port(
                        type=PortEnum.SOURCE,
                        position=PositionEnum.RIGHT,
                        port_type=PortTypeEnum.DATASET,
                        label="out",
                    ),
                ],
            ),
            version="1.0.0",
        )

    def run(self, inputs: dict, parameters: dict, ctx: NodeContext) -> dict:
        key = ctx.get_secret("api_key")
        # 값 자체는 노출하지 않고 길이만 출력으로 반환
        return {"out": pd.DataFrame({"key_len": [len(key)]})}
'''


def _write_node(tmp_path: Path) -> Path:
    node_file = tmp_path / "secret_node.py"
    node_file.write_text(_SECRET_NODE_SOURCE, encoding="utf-8")
    return node_file


def test_cli_injects_secret_end_to_end(tmp_path, capsys):
    node_file = _write_node(tmp_path)
    secret_value = "supersecret123"

    exit_code = main(["test", str(node_file), "-s", f"api_key={secret_value}"])

    out = capsys.readouterr().out
    assert exit_code == 0
    # 이름은 노출되지만 값은 stdout 에 절대 노출되지 않아야 한다
    assert "api_key" in out
    assert secret_value not in out


def test_cli_without_secret_fails_for_required_secret_node(tmp_path):
    node_file = _write_node(tmp_path)

    # secret 미주입 → get_secret 이 SecretNotAvailableError → run_test 가 1 반환
    exit_code = main(["test", str(node_file)])

    assert exit_code == 1


def test_cli_invalid_secret_format_fails(tmp_path):
    node_file = _write_node(tmp_path)

    exit_code = main(["test", str(node_file), "-s", "novalue"])

    assert exit_code == 1
