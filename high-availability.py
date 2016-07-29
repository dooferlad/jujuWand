#!/usr/bin/python3
import argparse

import re

from wand import bootstrap, clean, juju
from shelly import sudo, run


def main(controller, series):
    clean(controller)
    bootstrap(controller, params={
        'bootstrap-series': series
    })

    juju('switch {}:controller'.format(controller))
    juju('enable-ha')

    return

    juju_bin = run('which juju', quiet=True).rstrip()
    run('cp {} /tmp'.format(juju_bin), quiet=True)
    run('cp {}d /tmp'.format(juju_bin), quiet=True)

    out = juju('add-user testuser', quiet=True)
    for line in out.splitlines():
        if re.search('juju register', line):
            cmd = line
            break

    sudo('/tmp/juju {}'.format(cmd), user='testuser')
    sudo('/tmp/juju ensure-availability', user='testuser')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller', default='lxd')
    parser.add_argument('--series', default='xenial')
    args = parser.parse_args()
    main(args.controller, args.series)
