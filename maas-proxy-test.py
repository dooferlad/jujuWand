#!/usr/bin/python3

from wand import juju, bootstrap, bootstrapped
import time


def main():
    controller = 'maas-proxied'
    #juju destroy-environment -y maas-proxied ; juju bootstrap --upload-tools && juju deploy mysql
    if bootstrapped(controller):
        juju("kill-controller -y {}".format(controller))
        time.sleep(3)
    bootstrap(controller)
    juju('set-model-config http-proxy=192.168.0.22')
    juju('deploy mysql')

if __name__ == '__main__':
    main()
