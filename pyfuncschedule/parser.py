import ast
import inspect
from typing import Callable, List, Union, Any
from random import uniform

from .grammar import action_with_schedule, FuncCall, Schedule


class VFuncCall:

    def __init__(self, name: str, arguments: List[Any], func: Callable):
        self._func = func
        self._name = name
        self._arguments = arguments

    def _resolve_arguments(self):
        for x in self._arguments:
            if isinstance(x, VFuncCall):
                yield x()
            else:
                yield x

    def __call__(self):
        return self._func(*self._resolve_arguments())

    def __str__(self):
        return f"{self._name}({','.join(str(arg) for arg in self._arguments)})"

    def __repr__(self):
        return str(self)


class VSchedule:

    def __init__(self, intervals, repeat):
        self._intervals = intervals
        self._repeat = repeat

    def __str__(self):
        return f"[{','.join(str(arg) for arg in self._intervals)}]:{self._repeat}"

    def __repr__(self):
        return str(self)

    def __iter__(self):
        for _ in range(self._repeat):
            for interval in self._intervals:
                if isinstance(interval, VSchedule):
                    yield from interval
                elif isinstance(interval, VFuncCall):
                    yield float(interval())
                else:
                    yield float(interval)


class VActionSchedule:

    def __init__(self, action: VFuncCall, schedule: VSchedule):
        self._action = action
        self._schedule = schedule

    def __iter__(self):
        _iter = iter(self._schedule)
        yield (next(_iter), None)  # get initial interval to schedule next call
        for interval in _iter:
            yield (interval, self._action())
        yield (None, self._action())  # final call to action

    def __str__(self):
        return f"{self._action}@{self._schedule}"

    def __repr__(self):
        return str(self)

    async def __aiter__(self):
        import asyncio

        try:
            _iter = iter(self)
            # initial wait
            wait_time, _ = next(_iter)  # the first action is always None
            await asyncio.sleep(wait_time)

            while True:
                wait_time, action = next(_iter)
                if wait_time is None:
                    yield action
                    raise StopIteration
                future = asyncio.sleep(wait_time)
                yield action
                await future
        except StopIteration:
            pass

    async def asyncio_runner(self):
        """
        This is a simple schedule runner that uses `asyncio`.
        Given the nature of asyncio there is no guarentee that actions will execute on time,
        especially if there are long-running tasks in the asycnio event loop.
        """
        async for _ in self:
            pass


class ScheduleParser:
    def __init__(self, parser=None):
        self._parser = action_with_schedule() if parser is None else parser
        self._allowed_functions = {}
        self._allowed_actions = {}

    def register_action(self, action: Callable, name: str = None):
        """Add an action to the list of allowed actions."""
        if name is None:
            name = action.__name__
        self._allowed_actions[name] = action

    def register_function(self, func: Callable, name: str = None):
        """Add a function to the list of allowed functions."""
        if name is None:
            name = func.__name__
        self._allowed_functions[name] = func

    def parse(self, schedule: str):
        return self._parser.parseString(
            schedule,
            parse_all=True,
        )[0].as_list()

    def resolve(self, parse_result):
        return list(self._resolve_iter(parse_result))

    def _resolve_iter(self, parse_result):
        for action, schedule in parse_result:
            raction = ScheduleParser.resolve_action(
                action, self._allowed_actions, self._allowed_functions
            )
            rschedule = ScheduleParser.resolve_schedule(
                schedule, self._allowed_functions
            )
            yield VActionSchedule(raction, rschedule)

    @staticmethod
    def resolve_schedule(schedule, valid_funcs):
        repeat = ScheduleParser.resolve_repeat(schedule.repeat, valid_funcs)
        intervals = list(
            ScheduleParser.resolve_arguments(schedule.schedule, valid_funcs)
        )
        return VSchedule(intervals, repeat)

    @staticmethod
    def resolve_action(action, valid_actions, valid_funcs):
        name, args = action.identifier, action.arguments
        func = ScheduleParser.validate_func(name, args, valid_actions)
        args = list(ScheduleParser.resolve_arguments(args, valid_funcs))
        return VFuncCall(name, args, func)

    @staticmethod
    def resolve_func(func_call, valid_funcs):
        name, args = func_call.identifier, func_call.arguments
        func = ScheduleParser.validate_func(name, args, valid_funcs)
        args = list(ScheduleParser.resolve_arguments(args, valid_funcs))
        return VFuncCall(name, args, func)

    @staticmethod
    def resolve_repeat(repeat, valid_funcs):
        if isinstance(repeat, FuncCall):
            return ScheduleParser.resolve_func(repeat, valid_funcs)
        else:
            return repeat

    @staticmethod
    def resolve_arguments(arguments, valid_funcs):
        for arg in arguments:
            if isinstance(arg, FuncCall):
                yield ScheduleParser.resolve_func(arg, valid_funcs)
            elif isinstance(arg, Schedule):
                yield ScheduleParser.resolve_schedule(arg, valid_funcs)
            else:
                yield arg

    @staticmethod
    def validate_func(name, args, valid_funcs):
        if name not in valid_funcs:
            raise ValueError(f"Unregistered function: {name}")
        func = valid_funcs[name]

        sig = inspect.signature(func)
        # Determine if this is an instance method (which has 'self' as the first parameter)
        params = list(sig.parameters.values())
        if params and params[0].name == "self":
            # Adjust the signature by excluding the first parameter ('self')
            sig = sig.replace(parameters=params[1:])
        # Validate the arguments against the function's signature
        try:
            sig.bind(*args)
        except TypeError as e:
            error_msg = (
                f"Argument mismatch for function '{name}': {e}\n"
                f"Expected signature: {sig}\n"
                f"Provided arguments: {[arg for arg in args]}"
            )
            raise ValueError(error_msg) from e
        return func
