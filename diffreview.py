#!/usr/bin/python3

import re


def main():
    ok_lines = [
        'multiwatcher.JobManageNetworking',
        'state.JobManageNetworking',
        '"fmt"',
        '"github.com/juju/juju/feature"',
        'feature.AddressAllocation',
        'container.ConfigIPForwarding',
        '"github.com/juju/juju/api/addresser"',
        'enableNAT',
        'maybeReleaseContainerAddresses',
        'releaseContainerAddresses',
        'feature.AddressAllocation',
        '"github.com/juju/juju/network"',
        '"net"',
        'AllocatableIPLow',
        'AllocatableIPHigh',
        'ConfigIPForwarding',
        'ConfigEnableNAT',
        '"github.com/juju/utils/featureflag"',
        '"github.com/juju/juju/provider"',
        'SupportsAddressAllocation',
        'const AddressAllocation',
        'AllocateAddress',
        'ReleaseAddress',
    ]
    line_number = 0
    start = {}
    ref = {}
    state = {'in func'}
    start_at = 0
    file_deleted = False

    with open('/home/dooferlad/Downloads/download') as f:
        for line in f.readlines():
            line_number += 1

            line = line.rstrip()
            if re.search('^\s*$', line[1:]):
                continue

            if line.startswith('diff --git '):
                state = {'context': '\n' + '-'*80 + '\n{} {}'.format(line_number, line)}
                ref[line_number] = line
                file_deleted = False
            elif line.startswith('index ') and ref.get(line_number-1):
                # git index line
                pass
            elif line.startswith('--- ') and ref.get(line_number-2):
                start[line_number] = line
            elif line.startswith('deleted file mode ') and ref.get(line_number-1):
                file_deleted = True
            elif line.startswith('+++ ') and ref.get(line_number-3):
                start[line_number] = line
            elif line.startswith('@@ ') and re.search('@@ .\d+,\d+ .\d+,\d+ @@', line):
                #print(line_number, line)
                if 'context' not in state:
                    state['context'] = ''
                state['context'] += '\n' + line

            else:
                if file_deleted:
                    continue

                if line.startswith('-'):
                    if re.search('^\s*//', line[1:]):
                        # ignore comments
                        continue

                    if 'buffered' not in state:
                        state['buffered'] = []
                    state['buffered'].append(line)

                    fstart = re.search('^(\s*)func ', line[1:])
                    pclose = re.search('^(\s*)}', line[1:])
                    if fstart:
                        state['in func'] = line_number
                        state['func indent'] = len(fstart.group(1))

                    elif state.get('in func') and pclose and state['func indent'] == len(pclose.group(1)):
                        state['in func'] = 0
                        state['buffered'] = []

                    elif state.get('in func') == line_number - 1:
                        state['in func'] = line_number

                    if state.get('in func'):
                        continue

                    for bline in state['buffered']:
                        ignore_print(bline, ok_lines, line_number, start_at, state)

                    state['buffered'] = []

                elif line.startswith('+'):
                    ignore_print(line, ok_lines, line_number, start_at, state)


def ignore_print(line, ok_lines, line_number, start_at, state):
    if line_number < start_at:
        return

    ok = False
    for l in ok_lines:
        if line.find(l) != -1:
            ok = True
            break
    if not ok:
        if state.get('context'):
            print(state['context'])
            del(state['context'])
        print(line)


if __name__ == '__main__':
    main()
