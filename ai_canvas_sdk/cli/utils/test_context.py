"""테스트용 NodeContext 구현."""

from __future__ import annotations

import sys
import uuid
from datetime import datetime

from ai_canvas_sdk.custom_node import LogLevel, NodeContext


class TestNodeContext(NodeContext):
    """
    테스트용 NodeContext.

    - 로그를 터미널에 출력
    - 진행률 표시
    - 취소는 항상 False
    """

    def __init__(
        self,
        execution_id: str | None = None,
        node_id: str | None = None,
        user_id: str | None = None,
        team_id: str | None = None,
        verbose: bool = True,
    ):
        self._verbose = verbose
        self._logs: list[tuple[LogLevel, str, datetime]] = []
        self._progress_history: list[tuple[float, datetime]] = []

        def log_callback(level: LogLevel, message: str) -> None:
            timestamp = datetime.now()
            self._logs.append((level, message, timestamp))
            if self._verbose:
                self._print_log(level, message, timestamp)

        def progress_callback(progress: float) -> None:
            timestamp = datetime.now()
            self._progress_history.append((progress, timestamp))
            if self._verbose:
                self._print_progress(progress)

        def cancel_check_callback() -> bool:
            # 테스트 환경에서는 항상 취소되지 않음
            return False

        super().__init__(
            execution_id=execution_id or f"test-{uuid.uuid4().hex[:8]}",
            node_id=node_id or "test-node",
            user_id=user_id,
            team_id=team_id,
            log_callback=log_callback,
            progress_callback=progress_callback,
            cancel_check_callback=cancel_check_callback,
        )

    def _print_log(self, level: LogLevel, message: str, timestamp: datetime) -> None:
        """로그를 터미널에 출력."""
        time_str = timestamp.strftime("%H:%M:%S")
        level_str = level.value.upper()

        # 레벨별 색상 (ANSI)
        colors = {
            "DEBUG": "\033[90m",  # 회색
            "INFO": "\033[94m",  # 파란색
            "WARNING": "\033[93m",  # 노란색
            "ERROR": "\033[91m",  # 빨간색
            "CRITICAL": "\033[91m\033[1m",  # 굵은 빨간색
        }
        reset = "\033[0m"

        color = colors.get(level_str, "")

        # stderr로 출력 (stdout과 분리)
        print(
            f"{color}[{time_str}] [{level_str}] {message}{reset}",
            file=sys.stderr,
        )

    def _print_progress(self, progress: float) -> None:
        """진행률을 터미널에 출력."""
        percentage = int(progress * 100)
        bar_length = 30
        filled = int(bar_length * progress)
        bar = "=" * filled + "-" * (bar_length - filled)

        # 같은 줄에 업데이트
        print(f"\r[PROGRESS] [{bar}] {percentage}%", end="", file=sys.stderr)

        # 100%면 줄바꿈
        if progress >= 1.0:
            print(file=sys.stderr)

    @property
    def logs(self) -> list[tuple[LogLevel, str, datetime]]:
        """기록된 로그 목록."""
        return self._logs.copy()

    @property
    def progress_history(self) -> list[tuple[float, datetime]]:
        """진행률 히스토리."""
        return self._progress_history.copy()

    def get_logs_by_level(self, level: LogLevel) -> list[str]:
        """특정 레벨의 로그만 반환."""
        return [msg for lvl, msg, _ in self._logs if lvl == level]

    def has_errors(self) -> bool:
        """에러 로그가 있는지 확인."""
        error_levels = {LogLevel.ERROR, LogLevel.CRITICAL}
        return any(lvl in error_levels for lvl, _, _ in self._logs)


def create_test_context(
    verbose: bool = True,
    execution_id: str | None = None,
    node_id: str | None = None,
) -> TestNodeContext:
    """
    테스트용 NodeContext를 생성합니다.

    Args:
        verbose: 로그/진행률을 터미널에 출력할지 여부
        execution_id: 실행 ID (기본값: 자동 생성)
        node_id: 노드 ID (기본값: "test-node")

    Returns:
        TestNodeContext 인스턴스
    """
    return TestNodeContext(
        verbose=verbose,
        execution_id=execution_id,
        node_id=node_id,
    )
