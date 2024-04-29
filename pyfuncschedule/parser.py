import asyncio
import inspect
from typing import Callable, List, Any
from .grammar import action_with_schedule, FuncCall as GFuncCall, Schedule as GSchedule
from .async_iter import _AsyncScheduleIterator

__all__ = ("ScheduleParser", "parse", "resolve", "Schedule")


class VFuncCall:

    def __init__(self, name: str, arguments: List[Any], func: Callable):
        self._func = func
        self._name = name
        self._arguments = arguments

    def _resolve(self, args: List[Any]):
        for arg in args:
            yield self._resolve_arg(arg)

    def _resolve_arg(self, arg: Any):
        if isinstance(arg, (str, float, int, bool)):
            return arg
        elif isinstance(arg, VFuncCall):
            return arg()
        elif isinstance(arg, (list, tuple)):
            return type(arg)(self._resolve_arg(x) for x in arg)
        elif isinstance(arg, dict):
            return {self._resolve_arg(k): self._resolve_arg(v) for k, v in arg.items()}
        assert False  # this should never happen...

    def __call__(self):
        # print("RESOLVE!")
        return self._func(*self._resolve(self._arguments))

    def __str__(self):
        return f"{self._name}({','.join(str(arg) for arg in self._arguments)})"

    def __repr__(self):
        return str(self)


def forever_iter():
    while True:
        yield None


class VSchedule:

    def __init__(self, intervals, repeat):
        self._intervals = intervals
        self._repeat = repeat
        assert self._repeat != 0  # TODO check this in the parser early...
        if self._repeat >= 0:
            self._repeat_iter = range(self._repeat)
        else:
            self._repeat_iter = forever_iter()

    def __str__(self):
        return f"[{','.join(str(arg) for arg in self._intervals)}]:{self._repeat}"

    def __repr__(self):
        return str(self)

    def __iter__(self):
        for _ in self._repeat_iter:
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
        for interval in _iter:
            yield (interval, self._action)

    def stream(self):
        return _AsyncScheduleIterator(self)

    def __str__(self):
        return f"{self._action}@{self._schedule}"

    def __repr__(self):
        return str(self)


class ScheduleParser:
    def __init__(
        self,
    ):
        self._parser = action_with_schedule()
        self._allowed_functions = {}
        self._allowed_actions = {}

    def get_allowed_actions(self):
        return self._allowed_actions

    def get_allowed_functions(self):
        return self._allowed_functions

    def register_action(self, action: Callable, name: str = None):
        """Add an action to the list of allowed actions."""
        if name is None:
            name = action.__name__
        if name in self._allowed_actions:
            raise ValueError(f"An action with {name} is already registered.")
        self._allowed_actions[name] = action

    def register_function(self, func: Callable, name: str = None):
        """Add a function to the list of allowed functions."""
        if name is None:
            name = func.__name__
        if name in self._allowed_functions:
            raise ValueError(f"A function with {name} is already registered.")
        self._allowed_functions[name] = func

    def parse(self, schedule: str):
        return parse(schedule, parser=self._parser)

    def resolve(self, parse_result) -> List["Schedule"]:
        return resolve(parse_result, self._allowed_actions, self._allowed_functions)


# TODO type hints for this
def parse(
    schedule: str,
    parser=None,
):
    parser = action_with_schedule() if parser is None else parser
    return parser.parseString(schedule, parse_all=True)[0].as_list()


def resolve(parse_result, actions, functions) -> List["Schedule"]:
    return list(_resolve_iter(parse_result, actions, functions))


def _resolve_iter(parse_result, allowed_actions, allowed_functions):
    for action, schedule in parse_result:
        raction = resolve_action(action, allowed_actions, allowed_functions)
        rschedule = resolve_schedule(schedule, allowed_functions)
        yield VActionSchedule(raction, rschedule)


def resolve_schedule(schedule, valid_funcs):
    repeat = resolve_repeat(schedule.repeat, valid_funcs)
    intervals = list(resolve_arguments(schedule.schedule, valid_funcs))
    return VSchedule(intervals, repeat)


def resolve_action(action, valid_actions, valid_funcs):
    name, args = action.identifier, action.arguments
    func = validate_func(name, args, valid_actions)
    args = list(resolve_arguments(args, valid_funcs))
    return VFuncCall(name, args, func)


def resolve_func(func_call, valid_funcs):
    name, args = func_call.identifier, func_call.arguments
    func = validate_func(name, args, valid_funcs)
    args = list(resolve_arguments(args, valid_funcs))
    return VFuncCall(name, args, func)


def resolve_repeat(repeat, valid_funcs):
    if isinstance(repeat, GFuncCall):
        return resolve_func(repeat, valid_funcs)
    else:
        return repeat


def resolve_arg(arg, valid_funcs):
    if isinstance(arg, GFuncCall):
        return resolve_func(arg, valid_funcs)
    elif isinstance(arg, GSchedule):
        return resolve_schedule(arg, valid_funcs)
    elif isinstance(arg, (str, int, float, bool)):
        return arg
    elif isinstance(arg, (list, tuple)):
        return type(arg)(resolve_arguments(arg, valid_funcs))
    elif isinstance(arg, dict):
        return {
            resolve_arg(k, valid_funcs): resolve_arg(v, valid_funcs)
            for k, v in arg.items()
        }
    else:
        raise ValueError(
            f"Invalid arg: {arg} of type {type(arg)} found during schedule resolution."
        )


def resolve_arguments(arguments, valid_funcs):
    for arg in arguments:
        yield resolve_arg(arg, valid_funcs)


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


# Type alias for schedule
Schedule = VActionSchedule
