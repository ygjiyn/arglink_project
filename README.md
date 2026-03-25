# The "arglink" Package


## Introduction

The `arglink` package provides tools that links arguments of a parser and a callable.
The core functions are:
- Setup a parser based on arguments of a callable
- Build a kwargs dict to call the callable using the parsing results

## Preparation

To use `arglink`, in the definition the callable,
each argument should either
- be assigned to a default value other than `None`, or
- have a type annotation.

Only `int`, `float`, `bool`, and `str` are supported.

Users should use `setup_arglink` to decorate the callable.
See the end of this documentation for an example.

`setup_arglink` accepts two optional parameters.
- help_messages
    - Help messages for parameters.
    - Keys are names of arguments and values are messages.
- ignore_patterns
    - A list of regular expression patterns.
    - Arguments matching any of those patterns will be ignored.
    - By default, "self", "cls", and one ends with "_" will be ignored.

## Usage

The core functions are:

- `setup_arglink`: It attaches attributes required by this package and analyze the callable.
    See the following example.
- `callable_to_parser`: Add the arguments of a callable to a parser.
- `parser_to_callable`: Build the kwargs dict for calling the callable from the parsing results.

If a class is decorated or passed, its `__init__` method will be analyzed. 

## Example

Import methods from `arglink`:

```python
from arglink import setup_arglink, callable_to_parser
```

Decorate the target callable and prepare the parser:

```python
>>> import typing
>>> @setup_arglink(
...     help_messages={
...         'var_1': 'help message for var_1',
...         'var_a': 'help message for var_a',
...         'var_f': 'help message for var_f'
...     }
... )
... class TargetClass:
...     def __init__(
...         self,
...         var_to_skip_1_: list,
...         var_to_skip_2_: list,
...         var_1: int,
...         var_2: float,
...         var_3: str,
...         var_a=1,
...         var_b=1.1,
...         var_c='',
...         var_d1: int | None = None,
...         var_d2: typing.Optional[int] = None,
...         var_e=True,
...         var_f=False,
...         var_to_skip_3_=''
...     ):
...         pass
>>> parser = argparse.ArgumentParser()
>>> callable_to_parser(obj=TargetClass, parser=parser)
>>> parser.print_help() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
```

The parser looks like:

```
usage: ... [-h] --var-1 INT --var-2 FLOAT --var-3 STR
                          [--var-a INT] [--var-b FLOAT] [--var-c STR]
                          [--var-d1 INT] [--var-d2 INT] [--var-e-toggle]
                          [--var-f-toggle]
<BLANKLINE>
options:
  -h, --help           show this help message and exit
<BLANKLINE>
arguments for "__main__.TargetClass.__init__":
  --var-1 INT          help message for var_1
  --var-2 FLOAT
  --var-3 STR
  --var-a INT          (default: 1) help message for var_a
  --var-b FLOAT        (default: 1.1)
  --var-c STR          (default: '')
  --var-d1 INT         (default: None)
  --var-d2 INT         (default: None)
  --var-e-toggle       (default: True)
  --var-f-toggle       (default: False) help message for var_f
```
