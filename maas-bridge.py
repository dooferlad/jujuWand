#!/usr/bin/python3
import argparse

from wand import bootstrap, clean, juju


def main(controller):
    clean(controller)
    bootstrap(controller, params={
        #'to': 'zoe.maas',
        #'keep-broken': '',
        #'config': 'bootstrap-timeout=2000',
    })
    juju('deploy mysql')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller', default='maas')
    args = parser.parse_args()
    main(args.controller)
