import asyncio
import time
from pyfuncschedule import ScheduleParser


async def main():

    def foo():
        return f"foo: {time.time() - start_time}"

    start_time = time.time()
    schedules_str = """foo()@[1]:3"""
    parser = ScheduleParser()
    parser.register_action(foo)
    schedule = parser.resolve(parser.parse(schedules_str))[0]
    async for x in schedule.stream():
        print(x)


asyncio.run(main())
