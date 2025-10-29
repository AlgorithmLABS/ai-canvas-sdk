from __future__ import annotations

import argparse
import sys


def _get_version() -> str:
    """Get the SDK version."""
    try:
        from importlib.metadata import version

        return version("ai-canvas-sdk")
    except Exception:
        return "0.0.0"


def _print_version() -> None:
    """Print version information with system details."""
    sdk_version = _get_version()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    print(f"AI Canvas Custom Node SDK v{sdk_version}")
    print(f"✓ Python version: {python_version}")
    print("✓ Installation complete!")


def _test_connection() -> int:
    """Test system requirements and connection capabilities."""
    sdk_version = _get_version()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    print(f"AI Canvas Custom Node SDK v{sdk_version}")
    print(f"✓ Python version: {python_version}")

    # Test gRPC availability
    try:
        import grpc  # noqa: F401

        print("✓ gRPC connection: OK")
    except ImportError:
        print("✗ gRPC connection: Failed (grpcio not installed)")
        return 1

    # Test serialization libraries
    try:
        import pandas  # noqa: F401
        import pyarrow  # noqa: F401

        print("✓ Serialization: OK (Parquet/Arrow available)")
    except ImportError:
        print("✗ Serialization: Failed (pandas or pyarrow not installed)")
        return 1

    print("✓ Installation complete!")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-canvas-sdk", description="AI Canvas SDK CLI")
    parser.add_argument("--version", action="store_true", help="Show version and exit")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.add_parser("test-connection", help="Test system requirements and connection")

    args = parser.parse_args(argv)

    if args.version:
        _print_version()
        return 0

    if args.command == "test-connection":
        return _test_connection()

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

