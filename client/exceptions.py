class BaseSignalRClientError(Exception):
    pass


class SignalRConnectionError(BaseSignalRClientError):
    pass


class SignalRInvalidMessageError(BaseSignalRClientError):
    pass
