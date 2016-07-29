#!/usr/bin/python3
import argparse

import time

from wand import bootstrap, clean, juju, wait


def main(controller, cloud, series):
    clean(controller)
    bootstrap(controller, cloud, params={
        'bootstrap-series': series
    })
    wait()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller', default='lxd')
    parser.add_argument('--cloud', default='lxd')
    parser.add_argument('--series', default='xenial')
    args = parser.parse_args()
    main(args.controller, args.cloud, args.series)
