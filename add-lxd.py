#!/usr/bin/python3
import argparse

from wand import bootstrap, clean, wait, juju


def main(stop, controller, hosts, guests, wait_between_guests, deploy):
    clean(controller)
    bootstrap(controller)

    wait()
    for i in range(hosts):
        juju('add-machine')
    wait()

    first = True
    for j in range(guests):
        for i in range(hosts):
            if not deploy:
                juju('add-machine lxd:{}'.format(i))

            else:
                # Deploy the Ubuntu charm instead of just adding a machine
                if first:
                    juju('deploy ubuntu --to lxd:{}'.format(i))
                    first = False
                else:
                    juju('add-unit ubuntu --to lxd:{}'.format(i))

        if wait_between_guests:
            wait()

    wait()

    if stop:
        clean(controller)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stop')
    parser.add_argument('--controller', default='lxd')
    parser.add_argument('--hosts', default=1, type=int)
    parser.add_argument('--guests', default=12, type=int)
    parser.add_argument('--wait')
    parser.add_argument('--deploy')
    args = parser.parse_args()
    main(args.stop, args.controller, args.hosts, args.guests, args.wait,
         args.deploy)

