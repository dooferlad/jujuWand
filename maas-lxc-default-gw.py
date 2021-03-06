#!/usr/bin/python3

from wand import *
import time

if __name__ == '__main__':
    run('go install  -v github.com/juju/juju/...')
    juju('destroy-environment maas -y', fail_ok=True)
    juju('switch maas')

    juju('bootstrap --upload-tools')
    juju(r'set-env logging-config=\<root\>=TRACE')
    wait()

    juju('add-machine lxc:0')
    #juju('add-machine')
    #juju('add-machine lxc:1')
    wait()
    time.sleep(3)

    juju('ssh 0/lxc/0 "route -n"')
    juju('ssh 0/lxc/0 "more /etc/network/interfaces"')
    juju('ssh 0/lxc/0 "ping -c3 8.8.8.8"')
