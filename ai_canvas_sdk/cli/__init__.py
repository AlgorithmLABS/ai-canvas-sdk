"""AI Canvas SDK CLI.

커스텀 노드 개발을 위한 CLI 도구입니다.

사용법:
    ai-canvas-sdk --version          버전 출력
    ai-canvas-sdk test <node.py>     노드 테스트
    ai-canvas-sdk test <node.py> --validate-only  스키마만 검증
"""

from __future__ import annotations

import argparse
import sys


def _print_version() -> None:
    try:
        from importlib.metadata import version

        print(version("ai-canvas-sdk"))
    except Exception:
        print("0.0.0")


def main(argv: list[str] | None = None) -> int:
    """CLI 메인 진입점."""
    parser = argparse.ArgumentParser(
        prog="ai-canvas-sdk",
        description="AI Canvas SDK CLI - 커스텀 노드 개발 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-canvas-sdk test hello_node.py
      노드 파일을 로드하고 테스트 실행

  ai-canvas-sdk test hello_node.py --validate-only
      스키마만 검증

  ai-canvas-sdk test hello_node.py --input data.json --params '{"message": "Hi"}'
      입력 데이터와 파라미터를 지정하여 테스트
""",
    )

    parser.add_argument(
        "--version",
        "-V",
        action="store_true",
        help="버전 출력",
    )

    # 서브커맨드 설정
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        description="사용 가능한 명령어",
    )

    # test 커맨드 등록
    from ai_canvas_sdk.cli.test import setup_parser as setup_test_parser

    setup_test_parser(subparsers)

    # 인자 파싱
    args = parser.parse_args(argv)

    # --version 처리
    if args.version:
        _print_version()
        return 0

    # 서브커맨드가 없으면 도움말 출력
    if not args.command:
        parser.print_help()
        return 0

    # 서브커맨드 실행
    if hasattr(args, "func"):
        return args.func(args)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
