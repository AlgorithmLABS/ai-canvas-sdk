"""커스텀 노드 SDK 예외 계층."""


class CustomNodeError(Exception):
    """커스텀 노드 SDK 의 기본 예외."""


class SecretNotAvailableError(CustomNodeError):
    """노드가 요청한 secret 이 실행 컨텍스트에 주입되어 있지 않을 때 발생.

    노드가 `required_secrets` 에 선언하지 않았거나, 플랫폼에서 값이 설정되지
    않은 경우 `NodeContext.get_secret(name)` 이 이 예외를 던진다. secret 값 자체는
    메시지에 포함하지 않는다(이름만).
    """
