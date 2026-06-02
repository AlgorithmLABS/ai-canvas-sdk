from __future__ import annotations

import re
from pathlib import Path

from ai_canvas_sdk.cli import main


ROOT = Path(__file__).resolve().parents[1]


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


def test_cli_help_matches_registered_commands(capsys) -> None:
    main([])
    captured = capsys.readouterr().out

    docs = "\n".join(
        (ROOT / rel).read_text(encoding="utf-8")
        for rel in (
            "docs/README.md",
            "docs/prd/unified-prd.md",
            "docs/getting-started/installation.md",
            "docs/getting-started/quick-start.md",
            "docs/getting-started/first-node.md",
            "docs/concepts/architecture.md",
            "docs/concepts/data-types.md",
            "docs/concepts/lifecycle.md",
            "docs/guides/basic-node-development.md",
            "docs/api-reference/custom-node-class.md",
            "docs/troubleshooting/faq.md",
        )
        if (ROOT / rel).exists()
    )

    assert "test" in captured
    assert not re.search(
        r"ai-canvas-sdk\s+(?!test\b)[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b",
        docs,
    )
    assert "--sample-data" not in docs
    assert "--debug" not in docs
