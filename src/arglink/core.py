"""
The "arglink" Package

Linking an argument parser and a callable.

Examples
----------
>>> import typing
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
...         var_d1: int | None = None,
...         var_d2: typing.Optional[int] = None,
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
                          [--var-d1 INT] [--var-d2 INT] [--var-e-store-false]
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
  --var-d1 INT         (default: None)
  --var-d2 INT         (default: None)
  --var-e-store-false
  --var-f-store-true   help message for var_f
"""

import inspect
import re

import argparse
import typing
from typing import Callable
import types


class _ArglinkTargetCallable(typing.Protocol):
    _arglink_help_messages: dict[str, str] | None
    _arglink_ignore_patterns: list[str]
    _arglink_callable_args_to_parser_args: dict[str, str]
    _arglink_callable_args_to_args_for_add_augment: dict[str, dict]
    _arglink_has_been_analyzed: bool


_F = typing.TypeVar('_F', bound=Callable[..., typing.Any])


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
        
        param_has_annotation = param.annotation is not param.empty
        param_has_default = param.default is not param.empty
        
        # First, extract the type of this parameter
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
        
        # Second, extract the default value of this parameter
        param_default_value = param.default if param_has_default else None
        
        arg_name = '--' + param.name.replace('_', '-')
        if obj._arglink_help_messages:
            param_help = obj._arglink_help_messages.get(param.name, '')
        else:
            param_help = ''
        
        args_for_add_augment_dict = {}

        if param_type == bool:
            if param_default_value == False or param_default_value is None:
                arg_name += '-store-true'

                args_for_add_augment_dict['args'] = [arg_name]
                args_for_add_augment_dict['kwargs'] = dict(
                    action='store_true',
                    help=param_help
                )

                obj._arglink_callable_args_to_parser_args[param.name] = \
                    param.name + '_store_true'
            else:
                arg_name += '-store-false'

                args_for_add_augment_dict['args'] = [arg_name]
                args_for_add_augment_dict['kwargs'] = dict(
                    action='store_false',
                    help=param_help
                )

                obj._arglink_callable_args_to_parser_args[param.name] = (
                    param.name 
                    + '_store_false'
                )
        else:
            if param_has_default:
                args_for_add_augment_dict['args'] = [arg_name]
                args_for_add_augment_dict['kwargs'] = dict(
                    type=param_type, 
                    default=param_default_value,
                    metavar=param_type.__name__.upper(),
                    help=(
                        f'(default: {repr(param_default_value)}) '
                        + param_help
                    )
                )
            else:
                args_for_add_augment_dict['args'] = [arg_name]
                args_for_add_augment_dict['kwargs'] = dict(
                    type=param_type, 
                    required=True,
                    metavar=param_type.__name__.upper(),
                    help=param_help
                )
            obj._arglink_callable_args_to_parser_args[param.name] = param.name
        
        obj._arglink_callable_args_to_args_for_add_augment[param.name] = (
            args_for_add_augment_dict
        )
    
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

    group = parser.add_argument_group(f'arguments for "{_get_obj_identifier(obj)}"')
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
    for callable_arg, parser_arg in (
        obj
        ._arglink_callable_args_to_parser_args
        .items()
    ):
        callable_kw_dict[callable_arg] = args[parser_arg]
    return callable_kw_dict


def _get_obj_identifier(obj: Callable) -> str:
    return f'{obj.__module__}.{obj.__qualname__}'


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)
