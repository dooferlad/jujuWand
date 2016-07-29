#!/usr/bin/python3

import argparse
from wand import bootstrap, clean, juju, wait


def main(file_name):
    with open(file_name) as f:

        fold_indent = 0

        for full_line in f.readlines():
            lines = full_line.replace('\\n', '\n')
            for line in lines.splitlines():
                # if line.find('DEBUG lxd client.go:67') != -1:
                #     continue
                # print(line, end='')
                go_index = line.find('go:')
                if go_index == -1:
                    #print(line, end='')
                    continue

                extra_index = line.find('### |')
                if extra_index != -1:
                    extra_index += 5
                start = max(extra_index, go_index)

                indent = start
                while line[indent] != ' ':
                    indent += 1

                start = indent
                indent = 0

                while len(line) > start + indent and line[start + indent] == ' ':
                    indent += 1

                # if indent > 24:
                #     continue

                if extra_index == -1:
                    continue

                fold_these = [
                    'mgo.GridFile{',
                    'mgo.Session{',
                    'mgo.Database{',
                    'time.Time{',
                    'CACert:'
                    'database: &state.database{',
                    'gfs: &mgo.GridFS{',
                    'state.State{',
                ]

                if fold_indent and indent > fold_indent:
                    continue
                else:
                    fold_indent = 0

                # Print the line, max 190 chars
                if len(line) > 190:
                    print(line[:190], '...')
                else:
                    print(line)

                # Check to see if we should fold following lines
                for s in fold_these:
                    n = line.find(s)
                    if n != -1:
                        if line[n-1] in [' ', '&']:
                            fold_indent = indent
                            print(' ' * (start + indent), '   <snip>')
                            break
                        else:
                            print(':-(')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    args = parser.parse_args()
    main(args.file)
