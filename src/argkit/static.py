import argparse
import re
import codecs

def transfer_1():
    parser = argparse.ArgumentParser(
        description=('Transfer a parameter definition string param, ... to '
                     '(prefix1)param(suffix1)=(prefix2)param(suffix2)(join-str)... '
                     'String annotations are not supported'))
    parser.add_argument('-p1', '--prefix1', type=str, default='', metavar='STR')
    parser.add_argument('-s1', '--suffix1', type=str, default='', metavar='STR')
    parser.add_argument('-p2', '--prefix2', type=str, default='', metavar='STR')
    parser.add_argument('-s2', '--suffix2', type=str, default='', metavar='STR')
    parser.add_argument('-j', '--join-str', type=str, default=',\n', metavar='STR')
    parser.add_argument('-i', '--input-file', type=str, 
                        default='argkit_in.txt', metavar='STR')
    parser.add_argument('-o', '--output-file', type=str, 
                        default='argkit_out.txt', metavar='STR')
    args = parser.parse_args()

    print(f'Input file: {args.input_file}')
    with open(args.input_file) as f_in:
        contents = f_in.read()

    func_param_string = re.sub(r'\s', '', contents)
    result_list = []
    for param_def in func_param_string.split(','):
        param_name = param_def.split('=')[0].split(':')[0]
        result_list.append(f'{args.prefix1}{param_name}{args.suffix1}={args.prefix2}{param_name}{args.suffix2}')
    
    print(f'Output file: {args.output_file}')
    with open(args.output_file, 'w') as f_out:
        f_out.write(codecs.decode(args.join_str, 'unicode_escape').join(result_list))


