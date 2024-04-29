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

    # async def __aiter__(self):
    #     if self._done:
    #         raise ValueError("This schedule already finished.")
    #     try:

    #         # initial wait
    #         wait_time, _ = next(self._schedule)  # the first action is always None
    #         await asyncio.sleep(wait_time)

    #         while True:
    #             wait_time, action = next(self._schedule)
    #             if wait_time is None:
    #                 self._done = True
    #                 yield (
    #                     action,
    #                     self._done,
    #                 )  # this is the final action in the schedule
    #                 raise StopIteration
    #             self._wait_future = asyncio.sleep(wait_time)
    #             yield (action, self._done)
    #             await self._wait_future
    #     except StopIteration:
    #         # if this happens for some reason other than the schedule being done...?
    #         self._done = True
    #     except asyncio.CancelledError:
    #         self._done = True

    # def close(self):
    #     self._done = True
    #     if self._wait_future:
    #         self._wait_future.cancel()
