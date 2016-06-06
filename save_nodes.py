#!/usr/bin/python3

import json
import yaml
from shelly import run


def main():
    settings_file_name = 'maas.yaml'
    with open(settings_file_name) as f:
        cfg = yaml.load(f)

    out = run('maas maas nodes list', quiet=True)
    print('.')
    nodes = json.loads(out)

    result = {}

    for node in nodes:
        hostname = node['hostname']
        if hostname.endswith('.maas'):
            hostname = hostname[0:-len('.maas')]

        pdu = json.loads(run('maas maas node power-parameters ' + node['system_id'], quiet=True))
        print('.')

        for i in node['interface_set']:
            result[i['mac_address']] = {
                'hostname': hostname,
                'pdu_index': int(pdu['power_address']),
            }
    cfg['nodes'] = result
    with open(settings_file_name, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False)


if __name__ == '__main__':
    main()
