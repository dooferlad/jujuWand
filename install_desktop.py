#!/usr/bin/python3
import os
from urllib.parse import urlparse
import shelly
import re
from textwrap import dedent


def set_ubuntu_mirror(r):
    apt_file = '/etc/apt/sources.list'
    apt = []
    with open(apt_file) as f:
        for line in f.readlines():
            line = re.sub('//.*ubuntu.com/',
                          '//{ubuntu_mirror}/'.format(**r.settings), line)
            apt.append(line)

    with open('new.sources.list', 'w') as f:
        f.writelines(apt)

    r.run('cp {} .'.format(apt_file))
    r.sudo('cp new.sources.list {}'.format(apt_file))


def set_apt_proxy(r):
    proxy = dedent("""\
    Acquire {
     Retries "0";
     HTTP { Proxy "{apt_proxy}"; };
    };
    """)

    with open('31proxy', 'w') as f:
        f.write(proxy)

    r.sudo('mv 31proxy /etc/apt/apt.conf.d/')


def download_and_run(r):
    for url, cmds in r.settings.get('download_and_run', {}).items():
        filename = os.path.basename(urlparse(url).path)
        filename = os.path.join('/tmp/boblify/', filename)
        try:
            os.makedirs('/tmp/boblify/')
        except OSError:
            pass

        shelly.download(url, filename)
        for cmd in cmds:
            shelly.run(cmd.format(filename=filename))


def main():
    r = shelly.Runner('desktop.yaml')
    settings = r.settings

    # # download_and_run(r)
    # set_ubuntu_mirror(r)
    # set_apt_proxy(r)
    #
    # shelly.install_ppas(settings['ppas'])
    # shelly.install_packages(settings['packages'] + ['gdebi'])
    #
    # # Need to have a source page and regexp to search HTML for latest .deb..?
    # shelly.install_debs(settings['download_debs'])

    download_and_run(r)

    # Get home directory
    # syncthing?

if __name__ == '__main__':
    main()
