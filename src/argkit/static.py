import argparse
import re

def modify_pattern_feed():
    parser = argparse.ArgumentParser(
        description='String annotations are not supported')
    parser.add_argument('-p', '--prefix', type=str, default='', metavar='STR')
    parser.add_argument('-s', '--suffix', type=str, default='', metavar='STR')
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
        result_list.append(f'{param_name}={args.prefix}{param_name}{args.suffix}')
    
    print(f'Output file: {args.output_file}')
    with open(args.output_file, 'w') as f_out:
        f_out.write(',\n'.join(result_list))

