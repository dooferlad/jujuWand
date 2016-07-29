#!/usr/bin/python3

from wand import bootstrap, clean, wait, status, juju
from shelly import run
from pprint import pprint
import re


def report(controller):
    clean(controller)
    bootstrap(controller)

    wait()

    machines = 1
    containers = 1

    for i in range(machines):
        juju('add-machine')
        for j in range(containers):
            juju('add-machine -m foo lxc:{}'.format(i))
            juju('add-machine -m bar lxc:{}'.format(i))

    wait()

    test_features()

    clean(controller)


def _run_recurse_worder(runner, test, children, results):
    if hasattr(runner, test):
        result = getattr(runner, test)()
    else:
        result = 'Error: Test not found'

    if children:
        results[test] = _run_recurse(runner, children)
        results[test]['.'] = result

    else:
        results[test] = result

    return results


def _run_recurse(runner, tests):
    results = {}

    if isinstance(tests, dict):
        for test, children in tests.items():
            results = _run_recurse_worder(runner, test, children, results)

    elif isinstance(tests, list):
        children = None
        for test in tests:
            results = _run_recurse_worder(runner, test, children, results)

    else:
        results['.'] = 'Unable to use tests structure'

    return results


def test_features():
    nt = NetTests()
    tests = {
        'has_ipv4': [
            'ping_ipv4',
            'download_ipv4',
        ],
        'has_ipv6': None,
    }
    results = _run_recurse(nt, tests)

    pprint(results)


class NetTests:
    def __init__(self):
        self.cfg = self.iproute()

    def has_ipv4(self):
        for c in self.cfg.values():
            if c['name'] != 'lo':
                if 'inet' in c:
                    return True
        return False

    def has_ipv6(self):
        for c in self.cfg.values():
            if c['name'] != 'lo':
                if 'inet6' in c and c['inet6']['scope'] != 'link':
                    return True
        return False

    def ping_ipv4(self):
        return run('ping -c 3 8.8.8.8', fail_ok=True, quiet=True)[1] == 0

    def download_ipv4(self):
        return run('curl http://google.com', fail_ok=True, quiet=True)[1] == 0

    def iproute(self):
        ip = run('ip addr show', quiet=True)

        i = 0
        key = ''
        cfg = {}
        for line in ip.splitlines():
            x = re.search('(\d+):\s+(\S+):\s+<(.*?)>', line)
            if x:
                i = x.group(1)
                cfg[i] = {
                    'name': x.group(2),
                    'state': x.group(3).split(','),
                }

            elif line.startswith(' '):
                x = re.search('^(\s+)(.*)$', line)
                if x:
                    indent = len(x.group(1))
                    rest = x.group(2)
                    bits = rest.split()
                    if indent == 4:
                        key = bits[0]
                        bits[0] = 'addr'
                        cfg[i][key] = {}

                    for n in range(0, len(bits), 2):
                        if len(bits) == n+1:
                            cfg[i][key][bits[n]] = True
                        else:
                            cfg[i][key][bits[n]] = bits[n + 1]
                else:
                    print("couldn't parse indented line:")
                    print(line)
                    exit(1)
            else:
                if re.search('\S', line):
                    print("Couldn't parse line:")
                    print(line)
                    exit(1)

        return cfg


def main():
    clouds = [
        'lxd',
        # 'maas',
        # 'amzeu',
        # 'gce',
        # 'azure',
    ]
    for cloud in clouds:
        report(cloud)

if __name__ == '__main__':
    #main()
    test_features()
