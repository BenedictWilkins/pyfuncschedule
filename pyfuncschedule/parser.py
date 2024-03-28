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


class VSchedule:

    def __init__(self, intervals, repeat):
        self._intervals = intervals
        self._repeat = repeat


class ScheduleParser:
    def __init__(self, parser=None):
        self._parser = action_with_schedule() if parser is None else parser
        self._allowed_functions = {}
        self._allowed_actions = {}

    def add_function(self, name: str, func: Callable):
        """Add a function to the list of allowed functions."""
        self._allowed_functions[name] = func

    def parse(self, schedule: str):
        result = self._parser.parseString(
            schedule,
            parse_all=True,
        )[0].as_list()

        resolved = self._resolve_iter(result)

    def _resolve_iter(self, parse_result):
        for action, schedule in parse_result:
            print(action, schedule)
            raction = ScheduleParser.resolve_action(
                action, self._allowed_actions, self._allowed_functions
            )
            rschedule = ScheduleParser.resolve_schedule(
                schedule, self._allowed_functions
            )
            yield raction, rschedule

    @staticmethod
    def resolve_schedule(schedule, valid_funcs):
        repeat = schedule.repeat
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
    def resolve_arguments(arguments, valid_funcs):
        for arg in arguments:
            if isinstance(FuncCall, arg):
                yield ScheduleParser.resolve_func(arg, valid_funcs)
            else:
                yield arg

    @staticmethod
    def validate_func(name, args, valid_funcs):
        if name not in valid_funcs:
            raise ValueError(f"Unknown function: {name}")
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
