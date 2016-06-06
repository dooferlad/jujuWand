#!/usr/bin/python3

from wand import juju, bootstrap


def main():
    _, rc = juju("status -m lxd:default", fail_ok=True)
    if rc == 0:
        juju("kill-controller lxd -y")
    bootstrap('lxd')
    juju("upgrade-gui ~/Downloads/jujugui-2.1.1.tar.bz2")
    juju("gui")


if __name__ == '__main__':
    main()
