#!/usr/bin/python3

from shelly import *

settings = {
    'target': '192.168.0.27',
}

run('ssh {target} "mkdir -p /home/dooferlad/dev"'.format(**settings))
run('rsync -avP /home/dooferlad/dev/jujuWand    {target}:/home/dooferlad/dev/'.format(**settings))
run('rsync -avP /home/dooferlad/dev/trivial_pdu {target}:/home/dooferlad/dev/'.format(**settings))
