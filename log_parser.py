#!/usr/bin/python3

import argparse
import json
import re
from pprint import pprint


class Reader():
    def __init__(self, only_here_messages=False):
        self.only_here_messages = only_here_messages
        self.start_printing = [
            'lxd',
            'nic',
            'eth'
            'container',
            'Container'
        ]

        self.ignore = [
            'connecting to LXD remote',
            'cannot get "lxdbr0" addresses: route ip+net: no such network interface',
            '"lxdbr0" has addresses',
            'INFO juju.state addmachine.go:441 new machine',
            'SetSupportedContainers',
            'WatchContainers',
            'skipping observed IPv6 address',

            # Bugs..?
            'DEBUG juju.apiserver.common.networkingcommon types.go:529 updated observed address config for',
            'DEBUG juju.apiserver.common.networkingcommon types.go:533 merged config for',
        ]

        self.stop_printing = [
            ''
        ]

        self.countdown_reset = 10
        self.countdown = 0
        self.file_line_number = 0

    def read(self, file_name):
        self.fold_indent = 0

        with open(file_name) as f:
            for full_line in f.readlines():
                self.file_line_number += 1
                lines = full_line.replace('\\n', '\n')
                for line in lines.splitlines():
                    self._line(line)

    def _line(self, line):
        go_index = line.find('go:')
        if go_index == -1:
            # print(line, end='')
            return

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

        if self.only_here_messages and extra_index == -1:
            return

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

        if self.fold_indent and indent > self.fold_indent:
            return
        else:
            self.fold_indent = 0

        start = False
        start_reason = ""
        for find in self.start_printing:
            if line.find(find) != -1:
                start = True
                start_reason = find
                break

        if start:
            for find in self.ignore:
                if line.find(find) != -1:
                    start = False
                    break

        if start:
            if self.countdown == 0:
                print('\n{}: {}'.format(self.file_line_number, start_reason))
            self.countdown = self.countdown_reset

        if self.countdown > 0:
            self.countdown -= 1

            if 'juju.apiserver request_notifier.go' in line:

                find_json = re.search('(.*?)({.*})', line)
                if find_json:
                    try:
                        dat = json.loads(find_json.group(2))
                    except json.decoder.JSONDecodeError:
                        print('-' * 80)
                        print(line)
                        print(find_json.group(2))
                        exit(1)
                    print(find_json.group(1))
                    pprint(dat)
            else:
                self._print(line)
                if False:
                    # Print the line, max 190 chars
                    if len(line) > 190:
                        print(line[:190], '...')
                    else:
                        print(line)

                    if self.countdown == 0:
                        print('\n...\n')

        # Check to see if we should fold following lines
        for s in fold_these:
            n = line.find(s)
            if n != -1:
                if line[n - 1] in [' ', '&']:
                    self.fold_indent = indent
                    print(' ' * (start + indent), '   <snip>')
                    break
                else:
                    print(':-(')

    def _print(self, line):
        dbg = False
        if dbg:
            print(line)
            print('-' * 80)

        if line.find('{') == -1 or line.find('[') == -1:
            print(line)
            return

        start_index = 0
        index = -1
        self.bracket_stack = []
        for c in line:
            index += 1

            if c in ['[']:
                start_index = self.really_print(line, start_index, index)
                self.bracket_stack.append(c)
            elif c in ['{']:
                start_index = self.really_print(line, start_index, index)
                self.bracket_stack.append(c)
            elif c in ['}']:
                start_index = self.really_print(line, start_index, index+1)
                self.bracket_stack.pop()
            elif c in [']']:
                start_index = self.really_print(line, start_index, index)
                self.bracket_stack.pop()
            elif c in [',']:
                start_index = self.really_print(line, start_index, index)

        print(' ' * len(self.bracket_stack) + line[start_index:])
        if dbg:
            exit(0)

    def really_print(self, line, start_index, index):
        if len(self.bracket_stack) > 0:
            if start_index >= index:
                return start_index

            if index - start_index < 30:
                return start_index

        print(' ' * len(self.bracket_stack) + line[start_index:index])
        return index

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    args = parser.parse_args()
    #main(args.file)
    reader = Reader()
    reader.read(args.file)
