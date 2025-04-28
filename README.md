# The "argkit" Package


## Introduction

It is quite common to write a parser according to the definition of a class
and use this parser to obtain arguments to create an instance of this class.

The `argkit` provides tools for connecting arguments managed by a parser in `argparse` 
and those declared in the `__init__` method of a class.

Instead of manually maintaining the parser and class definition, 
it automatically generates the parser arguments of a class 
and creates the instance of this class using the parsed arguments.

## Preparation

Inside the `argkit` package, 
it uses the `inspect` module to analysis the definition of a class.

To use `argkit`, in the definition of the `__init__` method of the target class,
each argument, except the first `self` argument, should either
- be assigned to a default value other than `None`, or
- has a type annotation.

Only `int`, `float`, `bool`, and `str` are supported.

Only POSITIONAL_OR_KEYWORD parameters are supported, 
and there should be no `*`, `/`, `*args`, `**kwargs` in the definition of the `__init__` method.

Users could also define the following optional class variables and functions
to make further control.

- `_argkit_help_msgs`
    - (optional)
    - Help messages for parameters.
    - A dict whose keys are names of arguments and values are messages.

- `_argkit_ignore_list`
    - (optional)
    - A list containing arguments in the definition of the `__init__` method to be ignored.
    - Usually they would be common parameters or those needed to be handled manually.
    - One parameter should be either ignored or automatically handled.
    - User should take their own response that all duplicated parameters among different classes are ignored and properly handled.

- `_argkit_manual_handler`
    - (optional, function)
    - It will be called after the automatical handling of the args.
    - Users should take their own response that all ignored args are properly handled.
    - Its definition looks like follows:
    ```python
        @staticmethod
        def _argkit_manual_handler(parser): 
            pass
    ```

Besides, following class attributes will be created automatically:

- `_argkit_map_parser_to_cls`
    - (automatically created)
    - A dict whose keys and values are names of arguments in the parser and arguments in the class.

- `_argkit_args_for_add_augment`
    - (automatically created)
    - containing information used for the `add_argument` method.


## Usage

The core functions are:

- `cls_arg_to_parser` adds corresponding arguments to the parser based on the definition of the `__init__` method of the class.

- `parser_arg_to_cls` uses the parsed arguments to create an instance of the class.

Besides, some command line tools prefixed with "kit" (e.g. `kit1`, ...)
making string-based transformations are also provided in this package.

## Example

```python
class TargetClass:

    _argkit_help_msgs = {
        'var_1': 'help message for var_1',
        'var_a': 'help message for var_a',
        'var_f': 'help message for var_f'
    }

    _argkit_ignore_list = ['var_ignore_1', 'var_ignore_2']

    @staticmethod
    def _argkit_manual_handler(parser): 
        parser.add_argument('--ignore1', type=int, required=True)
        parser.add_argument('--ignore2', type=int, required=True)

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

The help message of the parser after calling the `cls_arg_to_parser` method looks like:

```
usage:  [-h] --var-1 INT --var-2 FLOAT --var-3 STR [--var-a INT] [--var-b FLOAT] [--var-c STR] [--var-d INT]
        [--var-e-store-false] [--var-f-store-true] --ignore1 IGNORE1 --ignore2 IGNORE2

options:
  -h, --help           show this help message and exit

arguments for class "TargetClass":
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
