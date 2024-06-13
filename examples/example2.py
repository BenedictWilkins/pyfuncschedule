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

    async def task(schedule):
        # notice that the functions are called automatically.
        # x is the result of a call to `foo` or `bar`.
        async for x in schedule.stream():
            print(x)

    tasks = []
    for schedule in schedules:
        tasks.append(asyncio.create_task(task(schedule)))
    await asyncio.gather(*tasks)


asyncio.run(main())
