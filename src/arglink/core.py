"""
The "arglink" Package

Linking an argument parser and a callable.

Examples
----------
>>> class TargetClass:
...     @setup_arglink(
...         help_messages={
...             'var_1': 'help message for var_1',
...             'var_a': 'help message for var_a',
...             'var_f': 'help message for var_f'
...         }
...     )
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
...         var_d: int = None,
...         var_e=True,
...         var_f=False,
...         var_to_skip_3_=''
...     ):
...         pass
>>> parser = argparse.ArgumentParser()
>>> callable_args_to_parser_args(obj=TargetClass.__init__, parser=parser)
>>> parser.print_help() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
usage: ... [-h] --var-1 INT --var-2 FLOAT --var-3 STR
                          [--var-a INT] [--var-b FLOAT] [--var-c STR]
                          [--var-d INT] [--var-e-store-false]
                          [--var-f-store-true]
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
  --var-d INT          (default: None)
  --var-e-store-false
  --var-f-store-true   help message for var_f
"""

import inspect
import re

import argparse
from typing import Callable, Any, Protocol, TypeVar


class _ArglinkTargetCallable(Protocol):
    _arglink_help_messages: dict[str, str] | None
    _arglink_ignore_patterns: list[str]
    _arglink_callable_args_to_parser_args: dict[str, str]
    _arglink_callable_args_to_args_for_add_augment: dict[str, dict]
    _arglink_has_been_analyzed: bool


_F = TypeVar('_F', bound=Callable[..., Any])


def setup_arglink(
    help_messages: dict[str, str] | None = None, 
    ignore_patterns: list[str] | None = None
) -> Callable[[_F], _F]:
    """
    Set up "arglink" for a callable.

    This function returns a decorator 
    adding attributes of meta information used by "arglink" to a callable.

    Parameters
    ----------
    help_messages : dict[str, str] or None, optional, default None.
        Help messages for parameters.
        Keys are names of arguments and values are messages.

    ignore_patterns : list[str] or None, optional, default None.
        A list containing regular expression patterns.
        The arguments matching any of those patterns will be ignored.
        This is useful when there are arguments needed to be handled manually.
        If ``None`` is passed, the following default pattern list will be used.
        Arguments "self", "cls", and any argument ends with "_" will be ignored.
        
        .. code:: python
            # default pattern list
            [r'^self$', r'^cls$', r'^.*_$']

    Returns
    ----------
    Callable[[_F], _F] : A decorator.
        It attaches attributes used by "arglink" to the callable.
        All those attributes are prefixed by "_arglink".

    Notes
    ----------
    About the attributes used by "arglink".

    ``_arglink_callable_args_to_parser_args`` is a dict such that

    - Keys: names of arguments in the definition of the callable. 
    - Values: names of attributes in the return value of ``parser.parse_args``,
        i.e., names of attributes of the `argparse.Namespace` object.
    
    ``_arglink_callable_args_to_args_for_add_augment`` is a dict such that
    
    - Keys: names of arguments in the definition of the callable. 
    - Values: dicts used for the `parser.add_augment` method, each of which is

    .. code:: python
        {
            'args': ['--arg-name'], 
            'kwargs': {'name': 'value', ...}
        }
    """
    def decorator(obj):
        obj._arglink_help_messages = help_messages
        if ignore_patterns is None:
            obj._arglink_ignore_patterns = [r'^self$', r'^cls$', r'^.*_$']
        else:
            obj._arglink_ignore_patterns = ignore_patterns
        obj._arglink_callable_args_to_parser_args = {}
        obj._arglink_callable_args_to_args_for_add_augment = {}
        obj._arglink_has_been_analyzed = False
        return obj
    return decorator


def analyze_callable_args(obj: _ArglinkTargetCallable) -> None:
    """
    Analyze the arguments of the definition of a callable.

    Parameters
    ----------
    obj : _ArglinkTargetCallable.
        A callable decorated by the decorator returned by ``setup_arglink``.

    Returns
    ----------
    None : nothing.
    """
    if obj._arglink_has_been_analyzed:
        return

    sig = inspect.signature(obj)

    for param in list(sig.parameters.values()):
        
        if any(re.fullmatch(p, param.name) for p in obj._arglink_ignore_patterns):
            continue

        assert param.kind == param.POSITIONAL_OR_KEYWORD, \
            (f'Error with {param.name}, '
             'only POSITIONAL_OR_KEYWORD parameters are supported.')
        
        this_param_has_annotation = param.annotation is not param.empty
        this_param_has_default = param.default is not param.empty
        
        # First, extract the type of this parameter
        # If the parameter has an annotation, use the annotation first
        if this_param_has_annotation:
            if isinstance(param.annotation, type):
                this_param_type = param.annotation
            else:
                raise RuntimeError(
                    f'The annotation of {param.name} is not supported. '
                    'The annotation should be an instance of type, such as int, float, etc.')
        # If no annotation, infer from its default value
        elif this_param_has_default:
            # None is not param.empty
            # However, since type(None) is <class 'NoneType'>,
            # which is not in (int, float, bool, str),
            # it will trigger a RuntimeError later
            # if the default value is None and there is no proper annotation
            this_param_type = type(param.default)
        else:
            raise RuntimeError(
                f'Parameter {param.name} should have an annotation or a default value.')

        if this_param_type not in (int, float, bool, str):
            raise RuntimeError(
                f'Error with {param.name}, only int, float, bool, str are supported.')
        
        # Second, extract the default value of this parameter
        this_param_default_value = param.default if this_param_has_default else None
        
        this_arg_name = '--' + param.name.replace('_', '-')
        if obj._arglink_help_messages:
            this_param_help = obj._arglink_help_messages.get(param.name, '')
        else:
            this_param_help = ''
        
        this_args_for_add_augment_dict = {}

        if this_param_type == bool:
            if this_param_default_value == False or this_param_default_value is None:
                this_arg_name += '-store-true'

                this_args_for_add_augment_dict['args'] = [this_arg_name]
                this_args_for_add_augment_dict['kwargs'] = dict(
                    action='store_true',
                    help=this_param_help
                )

                obj._arglink_callable_args_to_parser_args[param.name] = \
                    param.name + '_store_true'
            else:
                this_arg_name += '-store-false'

                this_args_for_add_augment_dict['args'] = [this_arg_name]
                this_args_for_add_augment_dict['kwargs'] = dict(
                    action='store_false',
                    help=this_param_help
                )

                obj._arglink_callable_args_to_parser_args[param.name] = \
                    param.name + '_store_false'
        else:
            if this_param_has_default:
                this_args_for_add_augment_dict['args'] = [this_arg_name]
                this_args_for_add_augment_dict['kwargs'] = dict(
                    type=this_param_type, 
                    default=this_param_default_value,
                    metavar=this_param_type.__name__.upper(),
                    help=(f'(default: {repr(this_param_default_value)}) ' + 
                          this_param_help))
            else:
                this_args_for_add_augment_dict['args'] = [this_arg_name]
                this_args_for_add_augment_dict['kwargs'] = dict(
                    type=this_param_type, 
                    required=True,
                    metavar=this_param_type.__name__.upper(),
                    help=this_param_help)
            obj._arglink_callable_args_to_parser_args[param.name] = \
                param.name
        
        obj._arglink_callable_args_to_args_for_add_augment[param.name] = \
            this_args_for_add_augment_dict
    
    obj._arglink_has_been_analyzed = True


def callable_args_to_parser_args(
    obj: _ArglinkTargetCallable, 
    parser: argparse.ArgumentParser
) -> None:
    """
    Add the arguments of a callable to a parser.

    Parameters
    ----------
    obj : _ArglinkTargetCallable.
        A callable decorated by the decorator returned by ``setup_arglink``.
    
    parser : argparse.ArgumentParser.

    Returns
    ----------
    None : nothing.
    """
    analyze_callable_args(obj)

    group = parser.add_argument_group(
        f'arguments for "{obj.__module__}.{obj.__qualname__}"'
    )
    for v in obj._arglink_callable_args_to_args_for_add_augment.values():
        group.add_argument(*v['args'], **v['kwargs'])


def parser_args_to_callable_kw_dict(
    args: argparse.Namespace | dict[str, int | float | bool | str], 
    obj: _ArglinkTargetCallable
) -> dict[str, int | float | bool | str]:
    """
    Get the kwargs dict for calling the callable from parsed arguments.

    Parameters
    ----------
    args : argparse.Namespace or dict[str, int | float | bool | str].
        The results of calling ``parser.parse_args``.
    
    obj : _ArglinkTargetCallable.
        A callable decorated by the decorator returned by ``setup_arglink``.

    Returns
    ----------
    dict[str, int | float | bool | str] : the kwargs dict of the callable.

    Examples
    ----------

    .. code:: python
        kwargs = parser_args_to_callable_kw_dict(args, obj)
        obj(extra_arg_1, extra_arg_2, **kwargs)
    """
    analyze_callable_args(obj)

    if not isinstance(args, dict):
        args = vars(args)
    callable_kw_dict: dict[str, int | float | bool | str] = {}
    for callable_arg, parser_arg in obj._arglink_callable_args_to_parser_args.items():
        callable_kw_dict[callable_arg] = args[parser_arg]
    return callable_kw_dict

if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)
