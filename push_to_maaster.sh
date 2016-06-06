#!/bin/bash

set -ex

cd /home/dooferlad/dev/jujuWand
rsync -vazP --progress --exclude-from=exclude.txt --delete /home/dooferlad/dev/jujuWand maaster:/home/dooferlad/dev/
rsync -vazP --progress --exclude-from=exclude.txt --delete /home/dooferlad/dev/trivial_pdu maaster:/home/dooferlad/dev/