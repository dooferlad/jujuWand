from wand import run
import json
import ipaddress


def maas(cmd):
    print('maas maas ' + cmd)
    out = run('maas maas ' + cmd, quiet=True)
    return json.loads(out)


class VLAN:
    def __init__(self, name, cidr, vid, interface):
        self.name = name
        self.network = ipaddress.IPv4Network(cidr)
        self.vid = vid
        self.interface = interface

    @property
    def network_address(self):
        return self.network.network_address

    @property
    def dynamic_start(self):
        return self.network_address + 10

    @property
    def dynamic_end(self):
        return self.network_address + 99

    @property
    def static_start(self):
        return self.network_address + 100

    @property
    def static_end(self):
        return self.network_address + 200

    @property
    def address(self):
        return self.network_address + 1

    @property
    def netmask(self):
        return self.network.netmask
