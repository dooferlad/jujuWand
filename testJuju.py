#!/usr/bin/python3
import concurrent.futures
import json
import os
import subprocess
import re
from argparse import ArgumentParser
from wand import run
from datetime import datetime
import fnmatch
from pprint import pprint

"""
Run juju tests.
1. Build Juju
2. If anything changed, run tests
3. If any tests didn't compile, exit
4. If any tests failed, re-run them.

Options:
 --force to run tests even if 'make install' didn't return any output.
 --rerun just re-run the failing tests from the last run, don't rebuild.
"""


JUJU_VCS = 'github.com/juju/juju'
JUJU_ROOT = os.path.join(os.environ['GOPATH'], 'src', JUJU_VCS)


def package_list():
    pattern = '*_test.go'
    packages = []
    src_len = len(JUJU_ROOT) + 1

    for root, dirs, files in os.walk(JUJU_ROOT):
        for filename in fnmatch.filter(files, pattern):
            p = root[src_len:]
            if p not in packages:
                packages.append(p)

    return sorted(packages)


def times():
    t = {}
    with open('/home/dooferlad/.jujuPackages.txt') as f:
        for line in f:
            s = re.search('^ok\s+github.com/juju/juju/(.*?)\s+([\d\.]+)s', line)
            if s:
                if float(s.group(2)) > 5:
                    t[s.group(1)] = float(s.group(2))

    pprint(t)


def compile_test_runner(package):
    binary_name = os.path.basename(package)
    binary_name += '.test'
    runner = os.path.join('/tmp', package, '_test', binary_name)

    if os.path.exists(runner):
        os.remove(runner)

    run('go test -c -i -o {} {}'.format(runner, package), fail_exits=True, quiet=True)

    return runner


def compile_and_run(package):
    logName = os.path.join('/tmp', package, 'out.txt')
    print('Testing {}'.format(package))

    with open(logName, 'w') as f:
        runner = compile_test_runner(package)
        out, rc = run(runner + '', write_to=f, fail_ok=True, quiet=True)
        if rc:

            print('  FAIL: {}\n{}\n'.format(package, out[:400]))
    os.remove(runner)
    return rc


def test_packages(pkgs):
    rc = 0
    packages = []
    for package in pkgs:
        if not package.startswith(JUJU_VCS):
            package = os.path.join(JUJU_VCS, package)
        packages.append(package)

    for p in packages:
        d = os.path.join('/tmp', p, '_test')
        if not os.path.exists(d):
            os.makedirs(d)

    failures = []

    with concurrent.futures.ProcessPoolExecutor(15) as executor:
        for package, result in zip(packages, executor.map(compile_and_run, packages)):
            #print('{}: {}'.format(package, result))
            if result:
                rc = 1
                failures.append(package)

    print('#' * 80)
    pprint(failures)

    return rc, failures


def test(args, db):
    long_tests = {
        'api': 9.926,
        'api/firewaller': 8.735,
        'api/provisioner': 10.475,
        'api/uniter': 34.885,
        'api/upgrader': 5.926,
        'apiserver': 141.927,
        'apiserver/client': 59.812,
        'apiserver/common': 10.367,
        'apiserver/firewaller': 5.664,
        'apiserver/metricsender': 5.502,
        'apiserver/provisioner': 20.643,
        'apiserver/storageprovisioner': 8.943,
        'apiserver/uniter': 54.406,
        'apiserver/upgrader': 7.856,
        'bzr': 6.002,
        'cmd/juju/action': 18.114,
        'cmd/juju/commands': 70.726,
        'cmd/juju/status': 17.68,
        'cmd/juju/system': 10.319,
        'cmd/jujud/reboot': 9.227,
        'container/lxc': 5.231,
        'downloader': 5.081,
        'environs/bootstrap': 47.446,
        'environs/configstore': 5.096,
        'featuretests': 53.464,
        'mongo': 19.99,
        'provider/ec2': 6.181,
        'provider/maas': 8.041,
        'provider/openstack': 36.273,
        'state': 230.395,
        'state/backups': 12.262,
        'state/presence': 5.551,
        'upgrades': 8.62,
        'utils/ssh': 5.196,
        'worker/addresser': 41.869,
        'worker/firewaller': 7.677,
        'worker/machiner': 11.263,
        'worker/peergrouper': 10.333,
        'worker/provisioner': 55.694,
        'worker/reboot': 10.65,
        'worker/uniter': 227.597,
        'worker/uniter/charm': 5.773,
        'worker/uniter/filter': 9.154,
        'worker/uniter/runner': 18.348,
    }

    start_time = datetime.now()
    try:
        install_out = run('go install  -v github.com/juju/juju/...')
    except subprocess.CalledProcessError as e:
        for line in e.output.splitlines():
            if not line.startswith(JUJU_VCS):
                print('!', line)
        return e.returncode
    output_filename = os.path.join(os.path.expanduser('~'),
                                   '.jujutestoutput.txt')
    rerun_filename = os.path.join(os.path.expanduser('~'),
                                  '.jujutestoutput_rerun.txt')

    print('Build duration:', datetime.now() - start_time)
    start_time = datetime.now()

    filename = None
    packages = []
    if args.fast:
        packages = package_list()
        # Start long tests first
        packages = sorted(packages, key=lambda p: long_tests.get(p, 0), reverse=True)
        rc, failures = test_packages(packages)
        # failures = ['github.com/juju/juju/state/presence',
        #             'github.com/juju/juju/utils/ssh',
        #             'github.com/juju/juju/cmd/jujud/agent',
        #             'github.com/juju/juju/cmd/pprof',
        #             'github.com/juju/juju/provider/joyent']
        # rc = 1
        print('Test duration:', datetime.now() - start_time)
        if rc:
            filename = '/tmp/all_failures.txt'
            with open(filename, 'w') as f:
                for p in failures:
                    logName = os.path.join('/tmp', p, 'out.txt')
                    with open(logName) as i:
                        f.write(i.read())
                        f.writelines([
                            '\nFAIL {} 0.0123456s\n\n'.format(p),
                            '# End of {}\n'.format(p),
                            '<>' * 40 + '\n\n',
                        ])

    elif args.changed:
        print('Testing changed packages')
        git_status = run('git status', quiet=True)
        # TODO: support new, deleted, modified, moved etc.
        packages_with_tests = package_list()
        for line in git_status.splitlines():
            mod = re.search('modified:\s+(.*)/.*?\.go$', line)
            if mod and mod.group(1) not in packages and mod.group(1) in packages_with_tests:
                packages.append(mod.group(1))

        # Sort packages to do long tests last
        # TODO: long tests first, in parallel...
        packages = sorted(packages, key=lambda p: long_tests.get(p, 0))
        print(packages)

        with open(output_filename, 'w') as f:
            for package in packages:
                package = 'github.com/juju/juju/' + package

                runner = compile_test_runner(package)
                run(runner, write_to=f, fail_ok=True)
                os.remove(runner)

        print('Test duration:', datetime.now() - start_time)
        filename = output_filename

    elif (len(install_out) or args.force) and not args.rerun:
        print('Testing everything')
        if os.path.isfile(rerun_filename):
            os.remove(rerun_filename)

        filename = output_filename
        with open(output_filename, 'w') as f:
            run('go test -i ./...', write_to=f, fail_exits=True)
            run('go test ./...', write_to=f, fail_ok=True)
            print('Test duration:', datetime.now() - start_time)
            start_time = datetime.now()

    else:
        print('Re-running failures from last test')
        # Don't have a new binary, so just re-run tests

        if db.get('empty'):
            del(db['empty'])
            # No old test DB, so parse the last output
            if os.path.isfile(rerun_filename):
                filename = rerun_filename
            elif os.path.isfile(output_filename):
                filename = output_filename

    unrecoverable = False
    if filename is not None:
        db['failures'] = {}
        with open(filename) as f:
            test_out = f.readlines()

        re_run = []
        re_run_tests = []
        for line in test_out:
            if line.startswith('FAIL:'):
                s = re.search('^FAIL:\s+.*\.go:\d+:\s+(.*)\s*$', line)
                if s:
                    print(s.group(1))
                    re_run_tests.append(s.group(1))
                else:
                    print(line)
                    return 0
            if not re.search('FAIL\s+github.*', line):
                continue

            s = re.search('FAIL\s+(.+?)\s+\[.*? failed\]', line)
            if s:
                unrecoverable = True
                db['failures'][s.group(1)] = ['.*']
                re_run_tests = []
                print(line)
            else:
                s = re.search('FAIL\s+(github.com.*)\s[\d\.]+s\s*$', line)
                db['failures'][s.group(1)] = re_run_tests
                re_run.append({
                    'package': s.group(1),
                    'tests': re_run_tests,
                })
                re_run_tests = []

    pprint(db)

    if len(db['failures'].keys()) == 0:
        return 0

    if not unrecoverable:
        print('Re-running failed tests...')
        failed = False
        remove_packages = []
        with open(rerun_filename, 'w') as f:
            for package, tests in db['failures'].items():
                failures = []
                name_search = re.search(r'github.com/juju/juju/(.*)', package)

                if name_search:
                    runner = compile_test_runner(package)
                    if len(tests):
                        for test in tests:
                            print(package, test)
                            out, rc = run('{} -check.f ^{}$'.format(runner, test), write_to=f, fail_ok=True, quiet=True)

                            if rc:
                                print(out[:400])
                                print('\n' + '-' * 80)

                            if args.stop_on_failure and rc:
                                os.remove(runner)
                                return rc

                            failed = failed or rc != 0
                            if rc:
                                failures.append(test)
                    else:
                        print(package)
                        out, rc = run(runner, write_to=f, fail_ok=True, quiet=True)

                        if rc:
                            print(out[:400])

                        if args.stop_on_failure and rc:
                            os.remove(runner)
                            return rc

                        failed = failed or rc != 0

                    os.remove(runner)

                if len(failures):
                    db['failures'][package] = failures
                elif failed:
                    db['failures'][package] = []
                elif package in db['failures']:
                    remove_packages.append(package)

        # Remove empty lists from database
        for package in remove_packages:
            del(db['failures'][package])

        print('Re-run duration:', datetime.now() - start_time)

        return failed
    else:
        print('Some failures are unrecoverable... not re-running.')

    return 0


def main():
    parser = ArgumentParser()
    parser.add_argument(
        '--force', action='store_true',
        help='Normally will only run if go build results in some output. This forces a complete run.')
    parser.add_argument(
        '--fast', action='store_true',
        help='[experimental] Run slow packages first. Later may try and split up large packages for increased parallelism.')
    parser.add_argument(
        '--rerun', action='store_true',
        help='Re-runs the tests that failed last time.')
    parser.add_argument(
        '--changed', action='store_true',
        help='Run tests in packages with changed files.')
    parser.add_argument(
        '--stop-on-failure', action='store_true',
        help='Abort testing as soon as a failure is detected.')
    args = parser.parse_args()

    os.chdir(JUJU_ROOT)

    # We store test results in a JSON blob.
    db_filename = os.path.join(os.path.expanduser('~'), '.jujutest.json')
    if os.path.exists(db_filename):
        with open(db_filename) as f:
            db = json.load(f)
    else:
        db = {
            'failures': {},
            'empty': True,
        }

    rc = test(args, db)
    with open(db_filename, 'w') as f:
        json.dump(db, f, sort_keys=True, indent=4)

    exit(rc)


if __name__ == '__main__':
    main()
