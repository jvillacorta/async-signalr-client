class BaseSignalRClientError(Exception):
    pass


class SignalRConnectionError(BaseSignalRClientError):
    pass


class SignalRInvalidMessageError(BaseSignalRClientError):
    pass


class SignalRCompletionServerError(BaseSignalRClientError):
    """
    Raises when a completion message contains an error
    """
    pass
