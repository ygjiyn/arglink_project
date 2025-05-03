import argparse
import re
import codecs

def transfer_single():
    parser = argparse.ArgumentParser(
        description=('Split a string, '
                     'transfer each splitted sub-string (s) to: '
                     '(prefix1)(s)(suffix1)(join-str)... '))
    
    parser.add_argument('-nw', '--remove-whitespace-store-false', action='store_false',
                        help='Do not remove whitespace')
    parser.add_argument('-np', '--parse-parameter-store-false', action='store_false',
                        help=('Input is not in the parameter definition stype, '
                              'i.e., do not split = (default value) and : (annotation)'))
    parser.add_argument('-ss', '--split-str', type=str, default=',', metavar='STR',
                        help='This string is used to split the input string')
    
    parser.add_argument('-p1', '--prefix1', type=str, default='', metavar='STR')
    parser.add_argument('-s1', '--suffix1', type=str, default='', metavar='STR')
    parser.add_argument('-j', '--join-str', type=str, default=',\n', metavar='STR')

    parser.add_argument('-i', '--input-file', type=str, 
                        default='argkit_in.txt', metavar='STR')
    parser.add_argument('-o', '--output-file', type=str, 
                        default='argkit_out.txt', metavar='STR')
    args = parser.parse_args()

    remove_whitespace = args.remove_whitespace_store_false
    parse_parameter = args.parse_parameter_store_false
    split_str = codecs.decode(args.split_str, 'unicode_escape')

    prefix1 = codecs.decode(args.prefix1, 'unicode_escape')
    suffix1 = codecs.decode(args.suffix1, 'unicode_escape')
    join_str = codecs.decode(args.join_str, 'unicode_escape')
    
    print(f'Input file: {args.input_file}')
    with open(args.input_file) as f_in:
        contents = f_in.read()

    if remove_whitespace:
        contents_processed = re.sub(r'\s', '', contents)
    else:
        contents_processed = contents
    
    result_list = []

    for s in contents_processed.split(split_str):
        if parse_parameter:
            s_processed = s.split('=')[0].split(':')[0]
        else:
            s_processed = s
        result_list.append(f'{prefix1}{s_processed}{suffix1}')
    
    print(f'Output file: {args.output_file}')
    with open(args.output_file, 'w') as f_out:
        f_out.write(join_str.join(result_list))


def transfer_double():
    parser = argparse.ArgumentParser(
        description=('Split a string, '
                     'transfer each splitted sub-string (s) to a "connected" format: '
                     '(prefix1)(s)(suffix1)(connect-str)(prefix2)(s)(suffix2)(join-str)... '))
    
    parser.add_argument('-nw', '--remove-whitespace-store-false', action='store_false',
                        help='Do not remove whitespace')
    parser.add_argument('-np', '--parse-parameter-store-false', action='store_false',
                        help=('Input is not in the parameter definition stype, '
                              'i.e., do not split = (default value) and : (annotation)'))
    parser.add_argument('-ss', '--split-str', type=str, default=',', metavar='STR',
                        help='This string is used to split the input string')
    
    parser.add_argument('-p1', '--prefix1', type=str, default='', metavar='STR')
    parser.add_argument('-s1', '--suffix1', type=str, default='', metavar='STR')
    parser.add_argument('-p2', '--prefix2', type=str, default='', metavar='STR')
    parser.add_argument('-s2', '--suffix2', type=str, default='', metavar='STR')
    parser.add_argument('-c', '--connect-str', type=str, default='=', metavar='STR')
    parser.add_argument('-j', '--join-str', type=str, default=',\n', metavar='STR')

    parser.add_argument('-i', '--input-file', type=str, 
                        default='argkit_in.txt', metavar='STR')
    parser.add_argument('-o', '--output-file', type=str, 
                        default='argkit_out.txt', metavar='STR')
    args = parser.parse_args()


    remove_whitespace = args.remove_whitespace_store_false
    parse_parameter = args.parse_parameter_store_false
    split_str = codecs.decode(args.split_str, 'unicode_escape')

    prefix1 = codecs.decode(args.prefix1, 'unicode_escape')
    suffix1 = codecs.decode(args.suffix1, 'unicode_escape')
    prefix2 = codecs.decode(args.prefix2, 'unicode_escape')
    suffix2 = codecs.decode(args.suffix2, 'unicode_escape')
    connect_str = codecs.decode(args.connect_str, 'unicode_escape')
    join_str = codecs.decode(args.join_str, 'unicode_escape')

    print(f'Input file: {args.input_file}')
    with open(args.input_file) as f_in:
        contents = f_in.read()

    if remove_whitespace:
        contents_processed = re.sub(r'\s', '', contents)
    else:
        contents_processed = contents
    
    result_list = []

    for s in contents_processed.split(split_str):
        if parse_parameter:
            s_processed = s.split('=')[0].split(':')[0]
        else:
            s_processed = s
        result_list.append(f'{prefix1}{s_processed}{suffix1}{connect_str}{prefix2}{s_processed}{suffix2}')
    
    print(f'Output file: {args.output_file}')
    with open(args.output_file, 'w') as f_out:
        f_out.write(join_str.join(result_list))

