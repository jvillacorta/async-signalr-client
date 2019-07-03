import time
import asyncio


class InvokeCompletionFuture(asyncio.Future):
    """
    Holds reference to an invoke completion message that may arrive in the future
    """

    def __init__(self, invocation_id, *args, time_to_live: int = 60 * 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.invocation_id = invocation_id
        self.ttl = time_to_live
        self.start_time = time.time()

    @property
    def expired(self):
        if time.time() > self.start_time + self.ttl:
            return True
        return False
