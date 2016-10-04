#!/usr/bin/python3

import subprocess
import yaml
import time
from datetime import datetime
from shelly import run


def wait_for_connection():
    while subprocess.call('timeout 5 juju status', shell=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT):
        time.sleep(5)


def v2():
    out = juju('version', silent=True)
    return out[0] == '2'


def _bootstrapped(controller):
    if v2():
        out, rc = juju('list-controllers', fail_ok=True, quiet=True)
        if controller in out:
            return True
    else:
        out, rc = run('timeout 1 juju status -e {}'.format(controller), fail_ok=True, quiet=True)
        if rc == 0:
            return True

    if 'ERROR Unable to connect to environment' in out:
        if not 'cannot connect to API servers without admin-secret' in out:
            return "dead"

        return False

    if rc != 0:
        return "dead"

    return False


def bootstrapped(controller):
    r = _bootstrapped(controller)
    if r in [True, False]:
        return r
    else:
        return True


def clean(controller):
    r = _bootstrapped(controller)
    if r == "dead":
        kill(controller, force=True)
    elif r:
        kill(controller)


def status():
    wait_for_connection()
    return yaml.load(run('juju status --format yaml', quiet=True))


def kill(controller, force=False):
    if v2():
        juju("kill-controller -y {} -t 10s".format(controller))
    else:
        cmd = 'destroy-environment {} -y'.format(controller)
        if force:
            cmd += ' --force'
        juju(cmd)

    time.sleep(15)


def juju(cmd, quiet=False, write_to=None, fail_ok=False, silent=False, offline=False):
    if silent:
        quiet = True
    if not silent:
        print("juju cmd:", cmd)
    offline_cmds = [
        'destroy-environment',
        'switch',
        'bootstrap',
        'version',
        'list-controllers',
    ]
    for c in offline_cmds:
        if cmd.startswith(c):
            offline = True
            break
    if not (offline or fail_ok):
        wait_for_connection()

    return run("juju " + cmd, quiet, write_to, fail_ok)


def watch(store, key, value, default=''):
    if store.get(key, default) != value:
        print(datetime.now(), key + ":", value)
        store[key] = value


def thing_state(m):
    return get(m, 'agent-state') or get(m, 'juju-status', 'current')


def get(thing, *keys):
    if len(keys) == 1:
        return thing.get(keys[0])

    if keys[0] in thing:
        return get(thing[keys[0]], *keys[1:])


def get_unit_state(unit):
    return (
        get(unit, 'agent-state') or
        get(unit, 'agent-status', 'current') or
        get(unit, 'service-status', 'current') or
        get(unit, 'juju-status', 'current')
    )


def deploy_bundle(name, version):
    if v2():
        return juju('deploy cs:bundle/{}-{}'.format(name, version))
    else:
        return juju('quickstart {}/{}'.format(name, version))


def wait(forever=False):
    keep_trying = True
    watching = {}

    retry_delay = 0
    while keep_trying or forever:
        time.sleep(retry_delay)
        retry_delay = 1
        try:
            s = status()
        except subprocess.CalledProcessError:
            continue
        keep_trying = False

        try:
            for name, m in s['machines'].items():

                agent_state = thing_state(m)
                watch(watching, name, agent_state, 'started')
                if agent_state != 'started':
                    keep_trying = True
                    continue

                ssms = m.get('state-server-member-status')
                if ssms and ssms != 'has-vote':
                    keep_trying = True
                    continue

                containers = m.get('containers')
                if containers:
                    for cname, c in containers.items():
                        agent_state = thing_state(c)
                        watch(watching, cname, agent_state, 'started')
                        if agent_state != 'started':
                            keep_trying = True

            if keep_trying:
                continue

            for service_name, service in s['services'].items():
                if 'units' not in service:
                    continue
                for unit in list(service['units'].values()):
                    name = unit['machine'] + ' ' + service_name
                    unit_state = get_unit_state(unit)
                    watch(watching, name, unit_state)

                    name += ' workload-status'
                    if unit['workload-status'].get('message'):
                        watch(watching, name, unit['workload-status']['message'])
                    else:
                        watch(watching, name, '')

                    if unit_state not in ['started', 'idle']:
                        keep_trying = True
                        continue
        except KeyError as e:
            print(e)
            print("continuing...")


def bootstrap(controller_name, cloud=None, params=None):
    if cloud is None:
        cloud = controller_name

    if not bootstrapped(controller_name):
        if v2():
            cmd = 'bootstrap {controller} {cloud} --debug --no-gui'
        else:
            cmd = 'bootstrap -e {controller} --upload-tools --debug'
        if params:
            for k, v in params.items():
                if v != '':
                    cmd += ' --{} "{}"'.format(k, v)
                else:
                    cmd += ' --{}'.format(k)

        juju(cmd.format(controller=controller_name, cloud=cloud))

    wait()


if __name__ == '__main__':
    start_at = 0
    if start_at <= 1:
        run('go install  -v github.com/juju/juju/...')
        juju('destroy-environment --force amzeu', fail_ok=True)
        juju('switch amzeu')
        juju('bootstrap --upload-tools')
        # juju('set-env logging-config=juju.state.presence=TRACE')
        juju(r'set-env logging-config=\<root\>=TRACE')
        wait()

    if start_at <= 2:
        # I don't know why, but deploying a charm before doing ensure-availability
        # seems to help us not get stuck in the waiting for has-vote state.
        juju('deploy ubuntu')
        wait()

    if start_at <= 3:
        juju('ensure-availability -n 3')
        wait()

    if start_at <= 4:
        # Need to wait until the Mongo servers actually do their HA thing. This
        # is not the same as status showing everything as started. Bother.
        #time.sleep(30)
        # 30 seconds seems to be more than enough time to let things settle.
        while True:
            try:
                juju('ssh 0 "sudo halt -p"')
                break
            except subprocess.CalledProcessError:
                time.sleep(5)

        time.sleep(60)
        juju('ensure-availability -n 3')
