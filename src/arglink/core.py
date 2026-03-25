"""
The "arglink" Package

Linking an argument parser and a callable.

Examples
----------
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
"""

import inspect
import re

import argparse
import typing
from typing import Callable, Any
import types


class _ArglinkTargetCallable(typing.Protocol):
    _arglink_help_messages: dict[str, str] | None
    _arglink_ignore_patterns: list[str]
    _arglink_callable_args_to_parser_args: dict[str, str]
    _arglink_callable_args_to_parser_configs: dict[str, dict]


_T = typing.TypeVar('_T')


def setup_arglink(
    help_messages: dict[str, str] | None = None, 
    ignore_patterns: list[str] | None = None
) -> Callable[[_T], _T]:
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
    Callable[[_T], _T] : A decorator.
        It attaches attributes used by "arglink" to the callable.
        All those attributes are prefixed by "_arglink".
        If it is a class, analyze its ``__init__`` method.
    """
    def decorator(any_obj):
        obj = _resolve_obj(any_obj)
        obj._arglink_help_messages = help_messages
        if ignore_patterns is None:
            obj._arglink_ignore_patterns = [r'^self$', r'^cls$', r'^.*_$']
        else:
            obj._arglink_ignore_patterns = ignore_patterns
        obj._arglink_callable_args_to_parser_args = {}
        obj._arglink_callable_args_to_parser_configs = {}
        _analyze_callable_args(obj)
        return any_obj
    return decorator


def callable_to_parser(
    obj: _ArglinkTargetCallable | Any, 
    parser: argparse.ArgumentParser
) -> None:
    """
    Add the arguments of a callable to a parser.

    Parameters
    ----------
    obj : _ArglinkTargetCallable or Any.
        A callable decorated by the decorator returned by ``setup_arglink``.
        If it is a class, analyze its ``__init__`` method.
    
    parser : argparse.ArgumentParser.

    Returns
    ----------
    None : nothing.
    """
    obj: _ArglinkTargetCallable = _resolve_obj(obj)
    group = parser.add_argument_group(f'arguments for "{_get_obj_identifier(obj)}"')
    for callable_arg, parser_arg in (
        obj
        ._arglink_callable_args_to_parser_args
        .items()
    ):
        parser_flag = _get_parser_flag(parser_arg)
        parser_config = obj._arglink_callable_args_to_parser_configs[callable_arg]
        group.add_argument(parser_flag, **parser_config)


def parser_to_callable(
    args: argparse.Namespace | dict[str, int | float | bool | str], 
    obj: _ArglinkTargetCallable | Any
) -> dict[str, int | float | bool | str]:
    """
    Get the kwargs dict for calling the callable from parsed arguments.

    Parameters
    ----------
    args : argparse.Namespace or dict[str, int | float | bool | str].
        The results of calling ``parser.parse_args``.
    
    obj : _ArglinkTargetCallable or Any.
        A callable decorated by the decorator returned by ``setup_arglink``.
        If it is a class, analyze its ``__init__`` method.

    Returns
    ----------
    dict[str, int | float | bool | str] : the kwargs dict of the callable.
    """
    obj: _ArglinkTargetCallable = _resolve_obj(obj)
    if not isinstance(args, dict):
        args = vars(args)
    callable_kwargs_dict: dict[str, int | float | bool | str] = {}
    for callable_arg, parser_arg in (
        obj
        ._arglink_callable_args_to_parser_args
        .items()
    ):
        callable_kwargs_dict[callable_arg] = args[parser_arg]
    return callable_kwargs_dict


def _analyze_callable_args(obj: _ArglinkTargetCallable) -> None:
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
    sig = inspect.signature(obj)

    for param in list(sig.parameters.values()):
        
        if any(re.fullmatch(p, param.name) for p in obj._arglink_ignore_patterns):
            continue

        if param.kind != param.POSITIONAL_OR_KEYWORD:
            raise RuntimeError(
                f'{param.name} in {_get_obj_identifier(obj)} is invalid, '
                'only POSITIONAL_OR_KEYWORD parameters are supported.'
            )
        
        param_has_annotation = param.annotation is not param.empty
        param_has_default = param.default is not param.empty
        
        # Extract the type of this parameter
        # If the parameter has an annotation, use the annotation first
        if param_has_annotation:
            # First, try to infer from the annotation
            if isinstance(param.annotation, str):
                raise RuntimeError(
                    f'Parameter {param.name} in {_get_obj_identifier(obj)} '
                    'uses a string annotation, which is not supported.'
                )
            
            annotation_origin = typing.get_origin(param.annotation)
            if annotation_origin is None:
                # simple case: annotation is a plain type/class
                param_type = param.annotation
            else:
                # Complicated case:
                # Only allow:
                # AcceptableType | None
                # Optional[AcceptableType]
                # Union[AcceptableType, None]
                annotation_acceptable = False
                if annotation_origin in (typing.Union, types.UnionType):
                    annotation_args = typing.get_args(param.annotation)
                    non_none = [t for t in annotation_args if t is not type(None)]
                    if len(non_none) == 1:
                        param_type = non_none[0]
                        annotation_acceptable = True
                if not annotation_acceptable:
                    raise RuntimeError(
                        f'Annotation of {param.name} in {_get_obj_identifier(obj)} '
                        f'({param.annotation}) is not supported.'
                    )
        elif param_has_default:
            # If no annotation, infer from its default value
            # None is not param.empty
            # However, since type(None) is <class 'NoneType'>,
            # which is not in (int, float, bool, str),
            # it will trigger a RuntimeError later
            # if the default value is None and there is no proper annotation
            param_type = type(param.default)
        else:
            raise RuntimeError(
                f'Parameter {param.name} should have '
                'either an annotation or a default value.'
            )

        if param_type not in (int, float, bool, str):
            raise RuntimeError(
                'Only int, float, bool, str are supported, but '
                f'{param.name} in {_get_obj_identifier(obj)} is {param_type}.'
            )
        
        # Extract the default value of this parameter
        param_default_value = param.default if param_has_default else None
        if param_type is bool and param_default_value is None:
            # For boolean args without default values / ``None``s by default,
            # set param_default_value to False
            param_default_value = False
        
        parser_arg = param.name
        if param_type is bool:
            parser_arg += '_toggle'
        obj._arglink_callable_args_to_parser_args[param.name] = parser_arg

        if obj._arglink_help_messages:
            param_help = obj._arglink_help_messages.get(param.name, '')
        else:
            param_help = ''

        if param_type is bool:
            parser_config = dict(
                action='store_false' if param_default_value else 'store_true',
                help=(
                    f'(default: {repr(param_default_value)}) '
                    + param_help
                )
            )
        else:
            if param_has_default:
                parser_config = dict(
                    type=param_type, 
                    default=param_default_value,
                    metavar=param_type.__name__.upper(),
                    help=(
                        f'(default: {repr(param_default_value)}) '
                        + param_help
                    )
                )
            else:
                parser_config = dict(
                    type=param_type, 
                    required=True,
                    metavar=param_type.__name__.upper(),
                    help=param_help
                )
        obj._arglink_callable_args_to_parser_configs[param.name] = parser_config


def _get_obj_identifier(obj: Callable) -> str:
    return f'{obj.__module__}.{obj.__qualname__}'


def _get_parser_flag(parser_arg: str) -> str:
    """
    Get corresponding flag in the parser from parser argument.

    Parameters
    ----------
    parser_arg : str
        The key in ``argparse.Namespace``, 
        corresponding to an argument of a callable.
        It can include "_"s, but "-"s are not allowed.

    Returns
    ----------
    str : the corresponding flag in the parser.
        It is generated by replacing "_"s with "-"s in ``parser_arg``
        and adding the prefix "--".
    """
    return '--' + parser_arg.replace('_', '-')


def _resolve_obj(obj: Any) -> Any:
    if inspect.isclass(obj):
        return obj.__init__
    else:
        return obj


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)
