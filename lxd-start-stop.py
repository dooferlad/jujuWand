#!/usr/bin/python3

from wand import bootstrap, clean, wait, status, juju
from pprint import pprint


def main():
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
            juju('add-machine -m foo lxc:{}'.format(i))
            juju('add-machine -m bar lxc:{}'.format(i))

    wait()
    juju('destroy-controller {} --destroy-all-models -y'.format(controller))
    clean(controller)

if __name__ == '__main__':
    main()
