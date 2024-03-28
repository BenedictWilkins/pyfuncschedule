# pyfuncschedule

A simple package that allows python functions to be repeatedly run according to a given schedule composed of a series of time intervals.

## Usage & Syntax

Function schedules are written as config files with a custom format. There is not yet a standardised file extention for such configuration files.

The simplest func schedule has the following syntax: 
```
FUNC(ARG1, ARG2, ...) @ [I1, I2, ...]:N
```
White spaces (including newlines and tabs) are ignored (unless part of `str` literals).

### Example 1 - Simple Schedule
```
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

`foo` will be executed at `t=1,3,4,` and continue until the schedule runner is terminated.
We can unpack this schedule as follows:
```
[1,2]:2 -> [1,3,4,6]
```
On the second running of `[1,2]:2` we treat the last execution timestamp as `0` and continue `[7,9,10,12]`. That is, nested schedules are unpacked _lazily_.

### Example 5 - Function Calls

Using static timings for schedules is useful in many scenarios, but in some cases we may like to determine these timings during execution. This can be done by registering functions to our schedule (see section TODO).
The syntax for this is the same as a function call in python.

```
foo() @ [uniform(0,1)]:*
```

This will execute `foo()` at some time sampled uniformly in the interval `[0,1]`. The `uniform` function is called repeatedly to produce new random intervals. The function is called to produce its value at the moment of the last execution of `foo`. If the function call is the first element in the schedule, it will be called at time `0` (`foo` is not executed at this time).


There are a number of useful built-in functions (see section TODO).

### Example 6 - Function Data

Many of the Python built-in data types: 'int','float','bool','str','list','dict' can be used as arguments to function calls. It is also possible to nest function calls, making it possible to pass around custom data types. 
```
foo(["a","b"]) @ [bar(baz(1), baz(2))]:*
```

### Example 7 - `time()`

The built-in `time()` function will return the time since the schedule began, it can be useful in some custom function implementations, for example: 

python```
def baz(t):
  return (t+1)*2
```
```
foo() @ [baz(time())]:*
```

Note that `time()` will always resolve to the time of the most recent call to `foo`, or at `t=0` if it is used at the beginning of the schedule.


## Parsing and Running Func Schedules





