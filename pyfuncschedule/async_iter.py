import asyncio

__all__ = ("_AsyncScheduleIterator",)


class _AsyncScheduleIterator:

    def __init__(self, schedule):
        super().__init__()
        self._schedule = iter(schedule)
        self._done = False

    def __aiter__(self):
        if self._done:
            raise ValueError("Iterator already completed.")
        return self

    async def __anext__(self):
        try:
            wait_time, action = next(self._schedule)
            await asyncio.sleep(wait_time)
            return action()  # call the action after waiting
        except StopIteration:
            self._done = True
            # pylint: disable = W0707
            raise StopAsyncIteration
