#!/usr/bin/python3
import os
import tempfile

import shelly
import json
import time
import argparse
from textwrap import dedent
import subprocess


class Runner(shelly.Runner):
    def maas(self, cmd, quiet=False):
        cmd = 'maas {profile} ' + cmd

        rc = 1
        tries_remaining = 20
        out = ''
        while rc and tries_remaining:
            tries_remaining -= 1
            out, rc = run(cmd.format(**self.settings), timeout=5,
                          fail_ok=True, quiet=quiet)
            if rc:
                print('command failed (rc={}), {} attempts remaining'.format(
                    rc, tries_remaining))
                time.sleep(5)
            else:
                time.sleep(0.5)

        try:
            return json.loads(out)
        except ValueError:
            return []


def setup_maas_server(r, settings):
    # We can find if there is an admin already created by asking for its API
    # key.
    settings['apikey'], rc = r.sudo('maas-region-admin apikey '
                                    '--username {username}', fail_ok=True)
    if rc > 0:
        # Our admin user doesn't exist - create it
        r.sudo('maas-region-admin createadmin --username={username} '
               '--password={password} --email={email}')

        # Fetch the API key if we need it.
        settings['apikey'] = r.sudo('maas-region-admin apikey '
                                    '--username {username}').rstrip()
    r.save_settings()

    while r.run('maas login {profile} http://{ipaddress}/MAAS {apikey}',
                fail_ok=True)[1]:
        time.sleep(3)

    # Reconfigure maas-proxy, or it won't work (1.8, really).
    # Reconfigure everything for good measure...
    pkgs = ['maas',
            'maas-cluster-controller',
            'maas-dhcp',
            'maas-proxy',
            'maas-region-controller-min',
            'maas-cli',
            'maas-common',
            'maas-dns',
            'maas-region-controller']
    for pkg in pkgs:
        r.sudo('dpkg-reconfigure --frontend noninteractive {}'.format(pkg))

    # r.maas('boot-resources import')


def setup_dns_and_keys(r):
    r.maas("maas set-config name=upstream_dns value='8.8.8.8 8.8.4.4'")
    keys = r.maas('sshkeys list')
    if len(keys) == 0:
        r.maas('sshkeys new key="{ssh_public_key}"')


def setup_network(r, settings):
    # Get information about node-group-interfaces that we need to set up the
    # network.
    node_groups = r.maas('node-groups list')
    r.settings['cluster_master_uuid'] = node_groups[0]['uuid']
    interface_list = r.maas('node-group-interfaces list {cluster_master_uuid}')

    # Find the interface we want to manage then copy the settings from our
    # settings YAML's network section over to MAAS.
    # Note that router_ip is used to set the default gateway, but isn't listed
    # by node-group-interface read!
    for interface in interface_list:
        if interface['ip'] == settings['network']['ip']:
            cmd = 'node-group-interface update {cluster_master_uuid} '
            cmd += interface['name']
            for k, v in settings['network'].items():
                cmd += ' {}={}'.format(k, v)
            r.maas(cmd)


# Setting up a mirror seems like a lot more trouble than using a well configured proxy
def setup_mirror(r):
    # Keep /var/www in my home directory so when I revert to an earlier
    # root snapshot I don't need to re-mirror
    r.sudo('rm -rf /var/www')
    r.sudo('ln -s /home/www /var/www')

    boot_sources = r.maas('boot-sources read')

    path = 'ephemeral-v2/releases/'
    url = 'http://{ipaddress}/maas/images/{path}'.format(path=path, **r.settings)
    found_mirror = False

    for bs in boot_sources:
        if int(bs['id']) == 1:
            # Delete the upstream source. At the moment this is too slow to use.
            r.maas('boot-source delete 1')
        if bs['url'] == url:
            found_mirror = True

    r.sudo("sstream-mirror"
           " --keyring=/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg"
           " https://images.maas.io/" + path +
           " /var/www/html/maas/images/" + path +
           " 'arch=amd64'"
           #" 'subarch~(generic|hwe-t|hwe-x)'"
           " 'release~(trusty|precise|xenial)'"
           " --max=1")

    if not found_mirror:
        r.maas('boot-sources create url=http://{ipaddress}/maas/images/' + path +
               ' keyring_filename=/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg')

    r.maas('boot-resources import')

    r.maas('maas set-config name=main_archive '
           'value="http://mirror.bytemark.co.uk/ubuntu/"')


def set_maas_defaults(r, settings):
    shelly.install_packages(['debconf-utils'])
    deb_config = [
        'maas-cluster-controller	maas-cluster-controller/maas-url	string	http://{ipaddress}/MAAS',
        'maas-region-controller-min	maas/default-maas-url	string	{ipaddress}',
    ]

    f = tempfile.NamedTemporaryFile(mode='w', delete=False)
    for cfg in deb_config:
        f.write(cfg.format(**settings) + '\n')
    f.close()

    r.sudo('debconf-set-selections ' + f.name)
    os.unlink(f.name)


def wait_for_quiet(silence=30):
    # Wait for the maas log to have no new entries for <silence> seconds.
    while time.time() < os.path.getmtime('/var/log/maas/maas.log') + silence:
        time.sleep(1)


def wait_for_boot_resources(r):
    old_len = 0
    while True:
        res = r.maas('boot-resources read', quiet=True)
        print(len(res))
        if len(res) > 3 and old_len == 0:
            # Looks like the import has already happened. Just return.
            return

        if old_len != len(res):
            old_len = len(res)
            time.sleep(30)
            continue

        if len(res) > 1:
            # Really don't know how many entries will turn up. Giving at least
            # 30 seconds between changes to this list should be enough.
            return


def setup_maas_nodes(r, settings):
    # If we haven't enlisted all the nodes, do so now
    nodes = r.maas('nodes list', quiet=True)
    if len(nodes) < len(settings['nodes']):
        r.run('{pdu_path}/all_off.py')
        r.run('{pdu_path}/all_on.py')

    # Wait for the nodes to appear
    # Since we index off MAC address, multi-NIC nodes show up more than once...
    unique_nodes = []
    for mac, n in settings['nodes'].items():
        if n['hostname'] not in unique_nodes:
            unique_nodes.append(n['hostname'])

    old_len = 0
    while len(nodes) < len(unique_nodes):
        if len(nodes) > old_len:
            print('found {} of {} nodes'.format(len(nodes), len(unique_nodes)))
            old_len = len(nodes)
        time.sleep(5)
        nodes = r.maas('nodes list', quiet=True)

    # We know the mac address of a network card in each node. Use that to find
    # per-node settings and set them.
    for node in nodes:
        for mac in node['macaddress_set']:
            node_settings = settings['nodes'].get(mac['mac_address'])

            if not node_settings:
                continue

            r.maas(
                'node update {system_id} power_type="amt" '
                'power_parameters_power_address={n} '
                'power_parameters_power_pass={n} '
                'hostname={hostname}'.format(
                    system_id=node['system_id'],
                    n=node_settings['pdu_index'],
                    hostname=node_settings['hostname']))

    r.run('{pdu_path}/all_off.py')
    r.sudo('rm /tmp/pdu_state.json')
    r.sudo('rm /tmp/pdu_lock')
    r.sudo('rm /tmp/log')
    r.maas('nodes accept-all')


def setup_maas_fabrics(r):
    fabric_name = None
    subnets = r.maas('subnets read')
    for subnet in subnets:
        if subnet['cidr'] == '192.168.1.0/24':
            fabric_name = subnet['vlan']['fabric']
            break

    fabrics = r.maas('fabrics read')
    for fabric in fabrics:
        if fabric['name'] == fabric_name:
            r.maas('fabric update {id} name=managed'.format(**fabric))
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default=1.9, type=float)
    args = parser.parse_args()

    runner = Runner('maas.yaml')
    settings = runner.settings

    set_maas_defaults(runner, settings)

    if args.version > 1.8:
        ppas = [
            'ppa:maas/stable',
        ]
        try:
            shelly.install_ppas(ppas)
        except subprocess.CalledProcessError:
            print("Couldn't find a MAAS PPA for this distro. Continuing without...")

    packages = [
        'maas',
        'wsmancli',
        'amtterm',
        'simplestreams',
        'ubuntu-cloudimage-keyring',
        'apache2',

        # Not strictly needed, but, well, I need them.
        'bwm-ng',
        'nethogs',
        'htop',
        'byobu',
    ]
    shelly.install_packages(packages)

    if not os.path.islink('/usr/local/bin/amttool'):
        runner.sudo('ln -s {pdu_path}/amttool /usr/local/bin/amttool')

    setup_maas_server(runner, settings)
    setup_dns_and_keys(runner)
    setup_mirror(runner)
    setup_network(runner, settings)

    wait_for_boot_resources(runner)
    print('waiting for quiet...')
    wait_for_quiet(90)
    print('lets import some nodes!')

    setup_maas_nodes(runner, settings)

    if args.version > 1.8:
        setup_maas_fabrics(runner)

    runner.save_settings()

    if args.version <= 1.8:
        print(dedent("""
              !!! You *must* set up:\n
               * The default route in the MAAS network
               * Upstream DNS
               * Your SSH key(s)
              """))


if __name__ == '__main__':
    main()
