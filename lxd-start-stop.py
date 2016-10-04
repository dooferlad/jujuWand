#!/usr/bin/python3
import argparse

from wand import bootstrap, clean, wait, status, juju
from pprint import pprint


def main(stop):
    controller = 'lxd'
    clean(controller)
    bootstrap(controller)

    wait()

    juju('add-model foo')
    juju('add-model bar')

    machines = 1
    containers = 2

    for i in range(machines):
        juju('add-machine -m foo')
        juju('add-machine -m bar')
        for j in range(containers):
            juju('add-machine -m foo lxd:{}'.format(i))
            juju('add-machine -m bar lxd:{}'.format(i))

    wait()
    if stop:
        juju('destroy-controller {} --destroy-all-models -y'.format(controller))
        clean(controller)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stop')
    args = parser.parse_args()
    main(args.stop)
