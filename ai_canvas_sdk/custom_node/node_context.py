from enum import Enum
from typing import Callable
from ai_canvas_sdk.custom_node.exceptions import SecretNotAvailableError


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NodeContext:
    """
    노드 실행 컨텍스트
    실행 환경 정보를 제공하고, 로그/진행률 보고 기능을 제공
    """

    def __init__(
        self,
        execution_id: str,
        node_id: str,
        user_id: str | None = None,
        team_id: str | None = None,
        secrets: dict[str, str] | None = None,
        # callback functions
        log_callback: Callable[[LogLevel, str], None] | None = None,
        progress_callback: Callable[[float], None] | None = None,
        cancel_check_callback: Callable[[], bool] | None = None,
    ):
        # 읽기 전용 메타데이터
        self._execution_id = execution_id
        self._node_id = node_id
        self._user_id = user_id
        self._team_id = team_id
        # 노드가 선언한 secret 값 (선언된 것만 주입됨; 전체 dict 는 외부에 노출하지 않는다)
        # 방어적 복사: 생성 후 호출자의 원본 dict 변경이 컨텍스트 상태를 오염시키지 못하게 한다.
        self._secrets = dict(secrets or {})
        # callback functions
        self._log_callback = log_callback
        self._progress_callback = progress_callback
        self._cancel_check_callback = cancel_check_callback

    # properties
    @property
    def execution_id(self) -> str:
        """현재 실행 ID"""
        return self._execution_id

    @property
    def node_id(self) -> str:
        """현재 노드 ID"""
        return self._node_id

    @property
    def user_id(self) -> str | None:
        """사용자 ID"""
        return self._user_id

    @property
    def team_id(self) -> str | None:
        """팀 ID"""
        return self._team_id

    # secrets
    def get_secret(self, name: str) -> str:
        """노드가 선언한 secret 값을 반환.

        Args:
            name: `required_secrets` 에 선언한 secret 이름

        Returns:
            str: secret 값

        Raises:
            SecretNotAvailableError: 해당 이름의 secret 이 주입되어 있지 않은 경우
        """
        if name not in self._secrets:
            raise SecretNotAvailableError(f"secret '{name}' 가 설정되어 있지 않습니다.")
        return self._secrets[name]

    # logging
    def log_debug(self, message: str):
        """디버그 로그 기록"""
        self._log(LogLevel.DEBUG, message)

    def log_info(self, message: str):
        """정보 로그 기록"""
        self._log(LogLevel.INFO, message)

    def log_warning(self, message: str):
        """경고 로그 기록"""
        self._log(LogLevel.WARNING, message)

    def log_error(self, message: str):
        """에러 로그 기록"""
        self._log(LogLevel.ERROR, message)

    def log_critical(self, message: str):
        """치명적 에러 로그 기록"""
        self._log(LogLevel.CRITICAL, message)

    # progress
    def progress(self, percentage: float):
        """
        진행률 업데이트

        Args:
            percentage: 진행률 (0.0 - 1.0)
        """
        if not 0.0 <= percentage <= 1.0:
            raise ValueError("진행률은 0.0에서 1.0 사이여야 합니다.")
        if self._progress_callback:
            self._progress_callback(percentage)

    def is_cancelled(self) -> bool:
        """
        실행이 취소되었는지 확인

        Returns:
            bool: 취소되었는지 여부(True: 취소됨, False: 취소되지 않음)
        """
        if self._cancel_check_callback:
            return self._cancel_check_callback()
        return False

    # helper functions
    def _log(self, level: LogLevel, message: str):
        """내부 로그 처리"""
        if self._log_callback:
            self._log_callback(level, message)
        elif level.value in ["error", "critical"]:
            # 콜백이 없으면 stdout 출력 (에러인 경우)
            prefix = f"[{level.value.upper()}]"
            print(f"{prefix} {message}")
