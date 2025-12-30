# The "arglink" Package


## Introduction

It is quite common to write a parser according to the definition a callable
and use this parser to obtain arguments to call this callable.

The `arglink` provides tools for connecting arguments managed by a parser in `argparse` 
and arguments declared in the definition of a callable, 
which eliminates the need for manually maintaining the parser and the definition of the callable.


## Preparation

Inside the `arglink` package, 
it uses the `inspect` module to analyze the callable.

To use `arglink`, in the definition the callable,
each argument should either
- be assigned to a default value other than `None`, or
- have a type annotation.

Only `int`, `float`, `bool`, and `str` are supported.

Only POSITIONAL_OR_KEYWORD parameters are supported, 
and there should be no `*`, `/`, `*args`, `**kwargs` in the definition.

Users should use `setup_arglink` to decorate the callable.
See the end of this documentation for an example.

`setup_arglink` accepts two optional parameters.
- help_messages
    - Help messages for parameters.
    - Keys are names of arguments and values are messages.
- ignore_patterns
    - A list containing regular expression patterns.
    - The arguments matching any of those patterns will be ignored.
    - This is useful when there are arguments needed to be handled manually.
    - If ``None`` is passed, the following default pattern list will be used.
    - Arguments "self", "cls", and any argument ends with "_" will be ignored.
        
    ``` python
        # default pattern list
        [r'^self$', r'^cls$', r'^.*_$']
    ```

## Usage

The core functions are:

- `setup_arglink`: Use it to add attributes used in this package.
    It only attaches attributes used by this package to the object.
    See the following example for its usage.
- `analyze_callable_args`: Analyze the arguments of the definition of a callable.
- `callable_args_to_parser_args`: Add the arguments of a callable to a parser.
- `parser_args_to_callable_kw_dict`: Get the kwargs dict for calling the callable from parsed arguments.

## Example

```python
from arglink.core import setup_arglink

class TargetClass:
    @setup_arglink(
        help_messages={
            'var_1': 'help message for var_1',
            'var_a': 'help message for var_a',
            'var_f': 'help message for var_f'
        }
    )
    def __init__(
        self,
        var_to_skip_1_: list,
        var_to_skip_2_: list,
        var_1: int,
        var_2: float,
        var_3: str,
        var_a=1,
        var_b=1.1,
        var_c='',
        var_d: int = None,
        var_e=True,
        var_f=False,
        var_to_skip_3_=''
    ):
        pass
```

Call `callable_args_to_parser_args`:

```python
import argparse
from arglink.core import callable_args_to_parser_args

parser = argparse.ArgumentParser()
callable_args_to_parser_args(obj=TargetClass.__init__, parser=parser)
parser.print_help() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
```

The help message looks like:

```
usage: ... [-h] --var-1 INT --var-2 FLOAT --var-3 STR
                          [--var-a INT] [--var-b FLOAT] [--var-c STR]
                          [--var-d INT] [--var-e-store-false]
                          [--var-f-store-true]

options:
  -h, --help           show this help message and exit

arguments for "__main__.TargetClass.__init__":
  --var-1 INT          help message for var_1
  --var-2 FLOAT
  --var-3 STR
  --var-a INT          (default: 1) help message for var_a
  --var-b FLOAT        (default: 1.1)
  --var-c STR          (default: '')
  --var-d INT          (default: None)
  --var-e-store-false
  --var-f-store-true   help message for var_f
```
