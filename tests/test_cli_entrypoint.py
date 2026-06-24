from __future__ import annotations

import re
from pathlib import Path

from ai_canvas_sdk.cli import main


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"


def _read_all_docs_markdown() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(DOCS_ROOT.rglob("*.md"))
    )


def _project_script_entry(name: str) -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(r"(?ms)^\[project\.scripts\]\s*(.*?)(?=^\[|\Z)", pyproject)
    assert section is not None, "[project.scripts] section is missing"

    entry = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\"([^\"]+)\"\s*$", section.group(1))
    assert entry is not None, f"{name} console script is missing"
    return entry.group(1)


def test_console_entrypoint_resolves_to_package_cli() -> None:
    assert _project_script_entry("ai-canvas-sdk") == "ai_canvas_sdk.cli:main"

    package_cli = ROOT / "ai_canvas_sdk" / "cli" / "__init__.py"
    assert package_cli.exists(), "package CLI module is missing"
    assert package_cli.is_file(), "package CLI entrypoint is not a file"
    assert not (ROOT / "ai_canvas_sdk" / "cli.py").exists(), (
        "remove the orphan module so the console entrypoint resolves only to the package CLI"
    )


def test_no_orphan_cli_module_shadows_package_cli(capsys) -> None:
    orphan_cli = ROOT / "ai_canvas_sdk" / "cli.py"
    assert not orphan_cli.exists(), (
        "remove the orphan module so the package CLI is the only CLI definition"
    )

    try:
        main(["test-connection"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected SystemExit")

    assert "invalid choice" in capsys.readouterr().err


def test_all_markdown_cli_command_examples_match_registered_surface(capsys) -> None:
    main([])
    captured = capsys.readouterr().out

    docs = _read_all_docs_markdown()

    assert "test" in captured
    assert not re.search(
        r"ai-canvas-sdk\s+(?!test\b)[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b",
        docs,
    )
    assert "--sample-data" not in docs
    assert "--debug" not in docs


def test_docs_do_not_overstate_cli_surface() -> None:
    docs = _read_all_docs_markdown()

    implemented_options = {
        "--class",
        "--validate-only",
        "--input",
        "-i",
        "--params",
        "-p",
        "--secret",
        "-s",
        "--output",
        "-o",
        "--verbose",
        "-v",
    }

    present_options = {option for option in implemented_options if option in docs}
    assert present_options == implemented_options, (
        "docs must document every implemented CLI option: "
        f"missing {sorted(implemented_options - present_options)}"
    )

    for forbidden in ("--sample-data", "--debug"):
        assert forbidden not in docs, f"docs must not mention stale option {forbidden}"

    for stale_phrase in (
        "CLI 명령어 전체 플로우",
        "모든 명령어 정상 동작",
        "Week 5: CLI Tools & Developer Experience",
    ):
        assert stale_phrase not in docs, f"docs must not overstate CLI scope via {stale_phrase!r}"
