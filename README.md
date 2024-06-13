# pyfuncschedule

A package that allows python functions to be repeatedly run according to a given schedule composed of a series of time intervals.

## Quick install

```pip install pyfuncschedule```

## Usage & Syntax

Function schedules are written as config files with a custom format. There is not as yet a standardised file extention for such configuration files, we might use `.fsch`.

The simplest func schedule has the following syntax: 
```
ACTION(ARG1, ARG2, ...) @ [I1, I2, ...]:N
```
White spaces (including newlines and tabs) are ignored (unless part of `str` literals).
Comments work similar to python and use `#` to being.

### Example 1 - Simple Schedule
```
# this is a comment
foo(1) @ [1,2,3]:1
```

Running this schedule will execute the function `foo` with arguments `1` at `t=1,3,6`. Notice that the schedule is specified in relative time in __seconds__ since the previous function execution (`int` or `float`).

### Example 2 - Repeating Schedule Blocks
```
foo() @ [1,2]:2
```

`foo` will be executed at `t=1,3,4,6`. The `:N` value specifies the number of times to repeat the given schedule block.

### Example 3 - Repeating Forever
```
foo() @ [1]:*
```

`foo` will be executed at `t=1,2,3,4,...` and continue until the schedule runner is terminated.

### Example 4 - Nesting Schedules

It is possible to nest schedules to acheive more complex timings.
```
foo() @ [[1,2]:2]:2
```
We can unpack this schedule as follows:
```
[1,2]:2 -> [1,2,1,2] -> t=[1,3,4,6]
[[1,2]:2]:2 -> [1,2,1,2,1,2,1,2] -> t=[1,3,4,6,7,9,10,12]
```
Nested schedules are unpacked _lazily_.

### Example 5 - Function Calls

Using static timings for schedules is useful in many scenarios, but in some cases we may like to determine these timings during execution. This can be done by registering functions to our schedule (see section TODO).
The syntax for this is the same as a function call in python.

```
foo() @ [uniform(0,1)]:*
```

This will execute `foo()` at some time sampled uniformly in the interval `[0,1]`. The `uniform` function is called repeatedly to produce new random intervals. The function is called to produce its value at the moment of the last execution of `foo`. If the function call is the first element in the schedule, it will be called at time `0` (`foo` is typically not executed at this time).

### Example 6 - Function Data

Many of the Python built-in data types: 'int','float','bool','str','list','dict' can be used as arguments to function calls. It is also possible to nest function calls, making it possible to pass around custom data types. 
```
foo(["a","b"]) @ [bar(baz(1), baz(2))]:*
```

## Parsing func schedules

parsing a schedule is easy:

1. create a parser
```python
from pyfuncschedule import ScheduleParser
parser = ScheduleParser()
```

2. register the functions that you want to use:
```python

def foo():
    ...
def bar():
    ...
# use register_action for the function you wish to call after each interval.
parser.register_action(foo)
# use register function for functions that are used in the intervals.
parser.register_function(bar)
```
3. define or load your schedules
```python
schedules_str = """foo1()@[bar(),2]:1"""
```
NOTE: as of version 0.1 schedules must be provided as a `str` there is no option for loading directly from a file.

4. parse and resolve
```python
schedules = parser.resolve(parser.parse(schedule_str))
```
This will parse the schedule and resolve any functions that have been registered. 

## Running func schedules

The result is a list of schedule objects which act like iterables providing `(interval, func)`. One way to run a given schedule is to iterate over it and to wait in a new thread, for example:

```python
for (interval, action) in schedules[0]:
    time.sleep(interval)
    action()
```

Instead, we can use `asyncio` and the `schedule.stream()` method, which will run the schedule in an `async` context.
```python
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
        async for x in schedule.stream():
            print(x)

    tasks = []
    for schedule in schedules:
        tasks.append(asyncio.create_task(task(schedule)))
    await asyncio.gather(*tasks)

asyncio.run(main())
```

The above creates an `asyncio` task for each schedule, this gives more control over how each schedule will be run. However if we have many schedules we might instead want all schedules to be "merged" into one. This can be acheived by using the `parser.stream(schedules)` method, see below:

```python
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
```

## Contributing

If you discover a bug or feel something is missing from this package please create an issue and feel free to contribute!





