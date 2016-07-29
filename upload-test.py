#!/usr/bin/python3
import argparse

import time

from wand import bootstrap, clean, juju, wait


def main(controller, series):
    clean(controller)
    bootstrap(controller, params={
        'bootstrap-series': series
    })

    #juju('deploy /home/dooferlad/charms/builds/resource-get-test')
    juju('deploy /home/dooferlad/charms/builds/resource-get-test --resource '
         'aresource=/home/dooferlad/a-file.bin')
    wait()
    #juju('attach resource-get-test name=/home/dooferlad/a-file.bin')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller', default='lxd')
    parser.add_argument('--series', default='xenial')
    args = parser.parse_args()
    main(args.controller, args.series)
