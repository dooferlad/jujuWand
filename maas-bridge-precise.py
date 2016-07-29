#!/usr/bin/python3

from wand import bootstrap, clean


def main():
    controller = 'maas-precise'
    clean(controller)
    bootstrap(controller, params={'to': 'zoe.maas'})

if __name__ == '__main__':
    main()
