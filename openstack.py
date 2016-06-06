#!/usr/bin/python3

from wand import bootstrap, clean, wait, status, deploy_bundle
from pprint import pprint


def main():
    controller = 'maas'  # bundle specifies series, so leave it unset.
    clean(controller)
    bootstrap(controller, params={'to': 'mal.maas'})
    deploy_bundle('openstack-base', 42)
    wait()
    pprint(status())

if __name__ == '__main__':
    main()
