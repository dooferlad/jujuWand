#!/usr/bin/python3

from wand import bootstrap, clean, wait, status, juju
from pprint import pprint


def main():
    controller = 'maas-xenial'  # bundle specifies series, so leave it unset.
    clean(controller)
    bootstrap(controller, params={'to': 'mal.maas'})

    wait()

    machines = 1
    containers = 2

    if machines > 1:
        juju('add-machine -n {}'.format(machines-1))
    for i in range(machines):
        for j in range(containers):
            juju('add-machine lxc:{}'.format(i))

    wait()

    # for i in range(1, 6):
    #     juju('remove-machine {} --force'.format(i))
    #
    # pprint(status())

if __name__ == '__main__':
    main()
