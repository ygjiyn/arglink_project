# The "argkit" Package


## Introduction

It is quite common to write a parser according to the definition a callable
and use this parser to obtain arguments to call this callable.

The `argkit` provides tools for connecting arguments managed by a parser in `argparse` 
and arguments declared in the definition of a callable, 
which eliminates the need for manually maintaining the parser and the definition of the callable.


## Preparation

Inside the `argkit` package, 
it uses the `inspect` module to analysis the callable.

To use `argkit`, in the definition the callable,
each argument should either
- be assigned to a default value other than `None`, or
- have a type annotation.

If the callable is a method in a class (e.g., the `__init__` method), 
or a class method (e.g., those decorated by `@classmethod`), 
setting the `skip_first` option to `True` in the provided functions 
could skip the first argument (e.g., `self`, `cls`).

Only `int`, `float`, `bool`, and `str` are supported.

Only POSITIONAL_OR_KEYWORD parameters are supported, 
and there should be no `*`, `/`, `*args`, `**kwargs` in the definition.

For each callable, users should maintain a dict, named `obj_dict`, a place to
store the results of analysis conducted by this package, 
as well as some user options.

A minimal `obj_dict` is just an empty dict `{}`.

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
    - Usually they would be common parameters or those needed to be handled manually.

- `manual_handler`
    - (optional, function)
    - It will be called after the automatical handling of the args.
    - It accepts a single argument `parser` and has no return values.
    - For example, `def manual_handler(parser): pass`.

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

- `analyze_callable_args`: Analyze the arguments of the definition of a callable.
- `add_callable_args_to_parser_args`: Add parser arguments 
    according to the definition of a callable.
- `transfer_parser_args_to_callable_kw_dict`: Get the kw dict for calling the callable from parsed args.

Besides, some command line tools prefixed with "kit" (e.g. `kit1`, ...)
making string-based transformations are also provided in this package.

## Example

```python

def argkit_manual_handler_target_class_init(parser): 
    parser.add_argument('--ignore1', type=int, required=True)
    parser.add_argument('--ignore2', type=int, required=True)

argkit_obj_dict_target_class_init = {
    'help_msgs': {
        'var_1': 'help message for var_1',
        'var_a': 'help message for var_a',
        'var_f': 'help message for var_f'
    },
    'ignore_list': [
        'var_ignore_1', 
        'var_ignore_2'
    ],
    'manual_handler': argkit_manual_handler_target_class_init
}

class TargetClass:
    def __init__(
        self,
        var_ignore_1,
        var_ignore_2,
        var_1:int,
        var_2:float,
        var_3:str,
        var_a=1,
        var_b=1.1,
        var_c='',
        var_d:int=None,
        var_e=True,
        var_f=False
    ):
        pass
```

Using functions in this package:

```python
import argparse
from argkit import add_callable_args_to_parser_args

parser = argparse.ArgumentParser()

add_callable_args_to_parser_args(
    obj=TargetClass.__init__, 
    obj_dict=argkit_obj_dict_target_class_init,
    skip_first=True,
    parser=parser)

parser.print_help()
```

Help message:

```
usage: argkit_example.py [-h] --var-1 INT --var-2 FLOAT --var-3 STR [--var-a INT] [--var-b FLOAT] [--var-c STR]
                         [--var-d INT] [--var-e-store-false] [--var-f-store-true] --ignore1 IGNORE1
                         --ignore2 IGNORE2

options:
  -h, --help           show this help message and exit

arguments for "TargetClass.__init__":
  --var-1 INT          help message for var_1
  --var-2 FLOAT
  --var-3 STR
  --var-a INT          help message for var_a
  --var-b FLOAT
  --var-c STR
  --var-d INT
  --var-e-store-false
  --var-f-store-true   help message for var_f
  --ignore1 IGNORE1
  --ignore2 IGNORE2
```
