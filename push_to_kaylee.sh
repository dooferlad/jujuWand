#!/bin/bash

set -ex

cd /home/dooferlad/dev/jujuWand
rsync -vazP --progress --exclude-from=exclude.txt --delete /home/dooferlad/dev/jujuWand kaylee.maas:/home/ubuntu
