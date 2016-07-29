#!/usr/bin/python3
import argparse

import time

from wand import bootstrap, clean, juju, wait


def main(controller, cloud, series):
    clean(controller)
    bootstrap(controller, cloud, params={
        'bootstrap-series': series,
        'to': 'wash.maas',
    })
    wait()

    # Since this is Juju 2.0 and we can't co-host (well, it isn't preferable)
    # add a machine (i.e. machine 0 in the default model).
    juju('add-machine mal.maas')
    wait()
    juju('add-machine lxd:0')
    wait()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller', default='maas')
    parser.add_argument('--cloud', default=None)
    parser.add_argument('--series', default='xenial')
    args = parser.parse_args()
    main(args.controller, args.cloud, args.series)
