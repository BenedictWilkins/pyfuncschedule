import time
import asyncio
from pyfuncschedule import ScheduleParser


async def main():

    start_time = time.time()
    schedules_str = """foo()@[1]:3 \n bar()@[2]:2"""
    parser = ScheduleParser()

    def foo():
        return f"foo: {time.time() - start_time}"

    def bar():
        return f"bar: {time.time() - start_time}"

    parser.register_action(foo)
    parser.register_action(bar)
    schedules = parser.resolve(parser.parse(schedules_str))
    # safe async iter context
    async with parser.stream(schedules) as stream:
        # iterate asynchronously
        async for x in stream:
            print(x)


asyncio.run(main())
