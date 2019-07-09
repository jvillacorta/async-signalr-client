class BaseSignalRClientError(Exception):
    """
    Base client exception class, all client exceptions will subclass from this
    """
    pass


class SignalRConnectionError(BaseSignalRClientError):
    """
    Error occurred while performing connection procedures or the connection drops
    """
    pass


class SignalRInvalidMessageError(BaseSignalRClientError):
    """
    Upstream or downstream messages are invalid or cannot be used by the specified protocol
    """
    pass


class SignalRCompletionServerError(BaseSignalRClientError):
    """
    Raises when a completion message contains an error
    """
    pass
