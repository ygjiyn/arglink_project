import inspect
import argparse


def attach_argkit_meta_info(obj_dict: dict, skip_first: bool, auto_skip: bool):
    '''\
    ## Add attributes of meta information to a callable object

    - `obj_dict`
        For the most simple case, it could be an empty dict `{}`.
        It contains all optional information used by functions in `argkit`.
        It could contain the following optional items:

        - `help_msgs`
            - (optional)
            - Help messages for parameters.
            - A dict whose keys are names of arguments and values are messages.

        - `ignore_list`
            - (optional)
            - A list containing arguments in the definition of the callable to be ignored.
            - Usually, it could contain those arguments which needed to be handled manually.

    - others
        Required information.

        - `skip_first`
            Whether skip the first argument or not.
            If the callable `obj` is a method or a class method of a class,
            set `skip_first` to `True` to skip the first argument (`self` or `cls`).
        
        - `auto_skip`
            Set `auto_skip` to `True` to skip unanalyzable parameters such that
            - no default values or default values are `None`s, and no type annotation, 
            - or type is not in (int, float, bool, str)
            instead of raising errors.
    '''
    def decorator(obj):
        obj._argkit_obj_dict = obj_dict
        obj._argkit_skip_first = skip_first
        obj._argkit_auto_skip = auto_skip
        return obj
    return decorator


def analyze_callable_args(obj: object):
    """\
    ## Analyze the arguments of the definition of a callable

    This function will analyze the definition of a callable and 
    add the following two keys to `obj_dict`.

    If the callable `obj` is a method or a class method of a class,
    set `skip_first` to `True` to skip the first argument (`self` or `cls`).

    Set `auto_skip` to `True` to skip unanalyzable parameters such that
    - no default values or default values are `None`s, and no type annotation,
    - or type is not in (int, float, bool, str)
    instead of raising errors.

    Keys added to `obj_dict`:

    - `dict_callable_args_to_parser_args`: 
        Keys: names of arguments in the definition of the callable. 
        Values: names of attributes in the return value of `parser.parse_args()`,
        i.e., names of attributes of the `argparse.Namespace` object.
    - `dict_callable_args_to_args_for_add_augment`:
        Keys: names of arguments in the definition of the callable. 
        Values: dicts used for the `parser.add_augment` method, each of which is
        ```python
        {
            'args': ['--arg-name'], 
            'kwargs': {'name': 'value', ...}
        }
        ```
    
    If keys above exists in `obj_dict`, they will be **overwriten**.
    """
    obj_dict = obj._argkit_obj_dict
    skip_first = obj._argkit_skip_first
    auto_skip = obj._argkit_auto_skip

    has_help_msgs = 'help_msgs' in obj_dict.keys()
    has_ignore_list = 'ignore_list' in obj_dict.keys()

    obj_dict['dict_callable_args_to_parser_args'] = {}
    obj_dict['dict_callable_args_to_args_for_add_augment'] = {}

    sig = inspect.signature(obj)

    start_from = 1 if skip_first else 0

    for param in list(sig.parameters.values())[start_from:]:
        
        if has_ignore_list and (param.name in obj_dict['ignore_list']):
            continue

        this_args_for_add_augment_dict = {}

        assert param.kind == param.POSITIONAL_OR_KEYWORD, \
            (f'Error with {param.name}, '
             'only POSITIONAL_OR_KEYWORD parameters are supported.')
        
        this_param_has_default = param.default is not param.empty

        if this_param_has_default and param.default is not None:
            this_param_type = type(param.default)
            this_param_default_value = param.default
        else:
            try:
                assert param.annotation is not param.empty, \
                    f'The annotation of {param.name} should not be empty.'
                assert isinstance(param.annotation, type), \
                    f'The annotation of {param.name} should be a type annotation.'
            except AssertionError:
                if auto_skip:
                    continue
                else:
                    raise
            this_param_type = param.annotation
            this_param_default_value = None

        try:
            assert this_param_type in (int, float, bool, str), \
                f'Error with {param.name}, only int, float, bool, str are supported.'
        except AssertionError:
            if auto_skip:
                continue
            else:
                raise
        
        this_arg_name = '--' + param.name.replace('_', '-')

        this_param_help = obj_dict['help_msgs'].get(param.name, '') if has_help_msgs else ''
        
        if this_param_type == bool:
            if this_param_default_value == False or this_param_default_value is None:
                this_arg_name += '-store-true'

                this_args_for_add_augment_dict['args'] = [this_arg_name]
                this_args_for_add_augment_dict['kwargs'] = dict(
                    action='store_true',
                    help=this_param_help
                )

                obj_dict['dict_callable_args_to_parser_args'][param.name] = \
                    param.name + '_store_true'
            else:
                this_arg_name += '-store-false'

                this_args_for_add_augment_dict['args'] = [this_arg_name]
                this_args_for_add_augment_dict['kwargs'] = dict(
                    action='store_false',
                    help=this_param_help
                )

                obj_dict['dict_callable_args_to_parser_args'][param.name] = \
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
            obj_dict['dict_callable_args_to_parser_args'][param.name] = \
                param.name
        
        obj_dict['dict_callable_args_to_args_for_add_augment'][param.name] = \
            this_args_for_add_augment_dict


def add_callable_args_to_parser_args(obj: object, parser: argparse.ArgumentParser):
    analyze_callable_args(obj)
    obj_dict = obj._argkit_obj_dict

    group = parser.add_argument_group(f'arguments for "{obj.__qualname__}"')
    for v in obj_dict['dict_callable_args_to_args_for_add_augment'].values():
        group.add_argument(*v['args'], **v['kwargs'])


def transfer_parser_args_to_callable_kw_dict(args: argparse.Namespace | dict, obj: object):
    """\
    ## Get the kw dict for calling the callable from parsed args
    
    For example:
    ```python
    callable_kw_dict = transfer_parser_args_to_callable_kw_dict(args, obj, obj_dict, skip_first)
    obj(extra_arg_1, extra_arg_2, **callable_kw_dict)
    ```
    """
    analyze_callable_args(obj)
    obj_dict = obj._argkit_obj_dict

    if not isinstance(args, dict):
        args = vars(args)
    callable_kw_dict = {}
    for callable_arg, parser_arg in obj_dict['dict_callable_args_to_parser_args'].items():
        callable_kw_dict[callable_arg] = args[parser_arg]
    return callable_kw_dict

