import argparse
import subprocess
import re

def feed():
    parser = argparse.ArgumentParser(
        description='NOTE: this command is under development, string annotations are not supported')
    parser.add_argument('-p', '--prefix', type=str, default='', metavar='STR')
    parser.add_argument('-s', '--suffix', type=str, default='', metavar='STR')
    parser.add_argument('-f', '--from-clipboard-command', type=str, 
                        default='pbpaste', 
                        metavar='STR')
    parser.add_argument('-t', '--to-clipboard-command', type=str,
                        default="echo '{result}' | pbcopy",
                        metavar='STR')
    args = parser.parse_args()

    p_from = subprocess.run(args.from_clipboard_command, capture_output=True)
    clipboard_contents = p_from.stdout.decode('UTF-8')
    func_arg_string = re.sub(r'\s', '', clipboard_contents)
    result_list = []
    for func_arg in func_arg_string.split(','):
        arg_name = func_arg.split('=')[0].split(':')[0]
        result_list.append(f'{arg_name}={args.prefix}{arg_name}{args.suffix}')
    subprocess.run(args.to_clipboard_command.format(result=',\n'.join(result_list)), shell=True)

