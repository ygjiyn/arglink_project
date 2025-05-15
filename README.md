# The "argkit" Package


## Introduction

It is quite common to write a parser according to the definition a callable
and use this parser to obtain arguments to call this callable.

The `argkit` provides tools for connecting arguments managed by a parser in `argparse` 
and arguments declared in the definition of a callable, 
which eliminates the need for manually maintaining the parser and the definition of the callable.


## Preparation

Inside the `argkit` package, 
it uses the `inspect` module to analyze the callable.

To use `argkit`, in the definition the callable,
each argument should either
- be assigned to a default value other than `None`, or
- have a type annotation.

Only `int`, `float`, `bool`, and `str` are supported.

Only POSITIONAL_OR_KEYWORD parameters are supported, 
and there should be no `*`, `/`, `*args`, `**kwargs` in the definition.

Users should use `attach_argkit_meta_info` to decorate the callable
by passing `obj_dict`, `skip_first`, `auto_skip`.
See the end of this documentation for an example.

The `obj_dict` is a place to
store the results of analysis conducted by this package, 
as well as some user options.
A minimal `obj_dict` is an empty dict `{}`, 
this is the case that none of the following options are needed.

If the callable is a method in a class (e.g., the `__init__` method), 
or a class method (e.g., those decorated by `@classmethod`), 
setting the `skip_first` option to `True` 
to skip the first argument (e.g., `self`, `cls`).

Set `auto_skip` to `True` to skip unanalyzable parameters such that
- no default values or default values are `None`s, and no type annotation, 
- or type is not in (int, float, bool, str)
instead of raising errors.

Users could include following items in the `obj_dict`
to make further control.
Do not create any of those keys if its corresponding value is empty.

- `help_msgs`
    - (optional)
    - Help messages for parameters.
    - A dict whose keys are names of arguments and values are messages.

- `ignore_list`
    - (optional)
    - A list containing arguments in the definition of the callable to be ignored.
    - Usually, it could contain those arguments which needed to be handled manually.

Besides, following keys will be added to the `obj_dict` 
during the analysis of the callable:

- `dict_callable_args_to_parser_args`: 
    - Keys: names of arguments in the definition of the callable. 
    - Values: names of attributes in the return value of `parser.parse_args()`,
    i.e., names of attributes of the `argparse.Namespace` object.

- `dict_callable_args_to_args_for_add_augment`:
    - Keys: names of arguments in the definition of the callable. 
    - Values: dicts used for the `parser.add_augment` method, each of which is
    ```python
    {
        'args': ['--arg-name'], 
        'kwargs': {'name': 'value', ...}
    }
    ```
    
If two keys above exists in `obj_dict`, they will be **overwriten**.


## Usage

The core functions are:

- `attach_argkit_meta_info`: A decorator factory function.
    Use it to add attributes used in this package.
    It only attaches attributes used by this package to the object.
    See the following example for its usage.
- `analyze_callable_args`: Analyze the arguments of the definition of a callable.
- `add_callable_args_to_parser_args`: Add parser arguments 
    according to the definition of a callable.
- `transfer_parser_args_to_callable_kw_dict`: Get the kw dict for calling the callable from parsed args.

Besides, some command line tools prefixed with "kit" (e.g. `kit1`, ...)
making string-based transformations are also provided in this package.

## Example

```python
from argkit import attach_argkit_meta_info

class TargetClass:

    @attach_argkit_meta_info(obj_dict={
        'help_msgs': {
            'var_1': 'help message for var_1',
            'var_a': 'help message for var_a',
            'var_f': 'help message for var_f'
        },
        'ignore_list': [
            'var_ignore_1', 
            'var_ignore_2'
        ]
    }, skip_first=True, auto_skip=True)
    def __init__(
        self,
        var_auto_skip_1,
        var_auto_skip_2:list,
        var_ignore_1:int,
        var_ignore_2:int,
        var_1:int,
        var_2:float,
        var_3:str,
        var_a=1,
        var_b=1.1,
        var_c='',
        var_d:int=None,
        var_e=True,
        var_f=False,
        var_auto_skip_3=None
    ):
        pass
```

Call `add_callable_args_to_parser_args`:

```python
import argparse
from argkit import add_callable_args_to_parser_args

parser = argparse.ArgumentParser()

add_callable_args_to_parser_args(
    obj=TargetClass.__init__, 
    parser=parser
)

parser.print_help()
```

Help message:

```
usage: argkit_example.py [-h] --var-1 INT --var-2 FLOAT --var-3 STR [--var-a INT] [--var-b FLOAT]
                         [--var-c STR] [--var-d INT] [--var-e-store-false] [--var-f-store-true]

options:
  -h, --help           show this help message and exit

arguments for "TargetClass.__init__":
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
