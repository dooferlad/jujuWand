#!/usr/bin/python3

from wand import bootstrap, clean, juju, wait, status
from pprint import pprint


def main():
    controllers = ['maas-trusty', 'maas-xenial', 'maas-precise']

    # first kill everything
    for controller in controllers + ['maas']:
        clean(controller)

    # now boot on everything
    for controller in controllers:
        bootstrap(controller, params={'to': 'zoe.maas'})
        # bootstrap(controller, params={'to': 'mal.maas'})
        juju('add-machine')
        wait()
        pprint(status())
        clean(controller)

if __name__ == '__main__':
    main()
