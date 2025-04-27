import inspect
import argparse


def cls_arg_to_parser(cls: object, parser: argparse.ArgumentParser):

    has_help_msgs = hasattr(cls, '_argkit_help_msgs')
    has_normal_map_parser_to_cls = hasattr(cls, '_argkit_normal_map_parser_to_cls')
    has_ignore_map_parser_to_cls = hasattr(cls, '_argkit_ignore_map_parser_to_cls')
    has_manual_handler = callable(getattr(cls, '_argkit_manual_handler', None))
    
    group = parser.add_argument_group(f'arguments for class "{cls.__name__}"')

    sig = inspect.signature(cls.__init__)

    if not has_normal_map_parser_to_cls:
        cls._argkit_normal_map_parser_to_cls = {}

    for p_obj in list(sig.parameters.values())[1:]:

        if has_ignore_map_parser_to_cls and \
            (p_obj.name in cls._argkit_ignore_map_parser_to_cls.values()):
            continue

        assert p_obj.kind == p_obj.POSITIONAL_OR_KEYWORD, \
            (f'Error with {p_obj.name}, '
             'only POSITIONAL_OR_KEYWORD parameters are supported.')
        
        this_param_has_default = p_obj.default is not p_obj.empty
        
        if this_param_has_default and p_obj.default is not None:
            this_param_type = type(p_obj.default)
            this_param_default_value = p_obj.default
        else:
            assert p_obj.annotation is not p_obj.empty, \
                f'The annotation of {p_obj.name} should not be empty.'
            assert isinstance(p_obj.annotation, type), \
                f'The annotation of {p_obj.name} should be a type annotation.'
            this_param_type = p_obj.annotation
            this_param_default_value = None
        
        assert this_param_type in (int, float, bool, str), \
            f'Error with {p_obj.name}, only int, float, bool, str are supported.'
        
        this_arg_name = '--' + p_obj.name.replace('_', '-')

        this_param_help = \
            cls._argkit_help_msgs.get(p_obj.name, '') if has_help_msgs else ''
        
        if this_param_type == bool:
            if this_param_default_value == False or this_param_default_value is None:
                this_arg_name += '-store-true'
                group.add_argument(this_arg_name, action='store_true', 
                                   help=this_param_help)
                cls._argkit_normal_map_parser_to_cls[
                    p_obj.name + '_store_true'] = p_obj.name
            else:
                this_arg_name += '-store-false'
                group.add_argument(this_arg_name, action='store_false', 
                                   help=this_param_help)
                cls._argkit_normal_map_parser_to_cls[
                    p_obj.name + '_store_false'] = p_obj.name
        else:
            if this_param_has_default:
                group.add_argument(this_arg_name, type=this_param_type, 
                                   default=this_param_default_value,
                                   metavar=this_param_type.__name__.upper(),
                                   help=this_param_help)
            else:
                group.add_argument(this_arg_name, type=this_param_type, 
                                   required=True,
                                   metavar=this_param_type.__name__.upper(),
                                   help=this_param_help)
            cls._argkit_normal_map_parser_to_cls[p_obj.name] = p_obj.name

    if has_manual_handler:
        cls._argkit_manual_handler(group)


def get_map_parser_to_cls(cls: object):
    has_normal_map_parser_to_cls = hasattr(cls, '_argkit_normal_map_parser_to_cls')
    assert has_normal_map_parser_to_cls, \
        'Attribute _argkit_normal_map_parser_to_cls is required.'
    has_ignore_map_parser_to_cls = hasattr(cls, '_argkit_ignore_map_parser_to_cls')
    map_parser_to_cls = {}
    map_parser_to_cls.update(cls._argkit_normal_map_parser_to_cls)
    if has_ignore_map_parser_to_cls:
        map_parser_to_cls.update(cls._argkit_ignore_map_parser_to_cls)
    return map_parser_to_cls


def parser_arg_to_cls(args: argparse.Namespace | dict, cls: object):
    map_parser_to_cls = get_map_parser_to_cls(cls)
    if not isinstance(args, dict):
        args = vars(args)
    this_cls_args = {}
    for parser_arg, cls_arg in map_parser_to_cls.items():
        this_cls_args[cls_arg] = args[parser_arg]
    return cls(**this_cls_args)

