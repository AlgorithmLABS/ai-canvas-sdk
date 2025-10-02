from __future__ import annotations

import argparse


def _print_version() -> None:
    try:
        from importlib.metadata import version

        print(version("ai-canvas-sdk"))
    except Exception:
        print("0.0.0")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-canvas-sdk", description="AI Canvas SDK CLI")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args(argv)

    if args.version:
        _print_version()
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
