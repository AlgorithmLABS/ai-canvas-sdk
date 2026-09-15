"""gRPC 메시지 크기 캡은 CNE/DAG 채널 옵션과 맞춰 50MiB 다."""

from __future__ import annotations

from pathlib import Path

from ai_canvas_sdk.serialization import DataSerializer

ROOT = Path(__file__).resolve().parents[1]


def test_grpc_size_limit_is_50_mib() -> None:
    assert DataSerializer.GRPC_SIZE_LIMIT == 50 * 1024 * 1024


def test_docs_match_50_mib_cap() -> None:
    docs = (ROOT / "docs" / "concepts" / "data-types.md").read_text(encoding="utf-8")
    assert "50 * 1024 * 1024" in docs
    assert "3 * 1024 * 1024" not in docs
