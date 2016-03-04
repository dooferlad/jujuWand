#!/usr/bin/python3
import json
import os
import subprocess
import re
from argparse import ArgumentParser
from wand import run
from datetime import datetime

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


def main(args, db):
    long_tests = {
        'state': 270,
        'mongo': 19,
    }
    start_time = datetime.now()
    try:
        install_out = run('go install  -v github.com/juju/juju/...')
    except subprocess.CalledProcessError as e:
        for line in e.output.splitlines():
            if not line.startswith('github.com/juju/juju/'):
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
    if args.changed:
        print('Testing changed packages')
        git_status = run('git status', quiet=True)
        # TODO: support new, deleted, modified, moved etc.
        for line in git_status.splitlines():
            mod = re.search('modified:\s+(.*)/.*?\.go$', line)
            if mod and mod.group(1) not in packages:
                packages.append(mod.group(1))

        # Sort packages to do long tests last
        # TODO: long tests first, in parallel...
        packages = sorted(packages, key=lambda p: long_tests.get(p, 0))
        print(packages)

        with open(output_filename, 'w') as f:
            for package in packages:
                run('GOMAXPROCS=32 go test -i github.com/juju/juju/' + package, write_to=f, fail_exits=True)
                run('GOMAXPROCS=32 go test github.com/juju/juju/' + package, write_to=f, fail_ok=True)

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

        if not os.path.exists(db_filename):
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
            if(not re.search('FAIL\s+github.*\n', line) and
               not line.startswith('# github.com')):
                continue

            if re.search('failed\]\s*$', line):
                # Build failed or setup failed. No point re-running, but need
                # to report
                unrecoverable = True
            elif line.startswith('# github.com'):
                unrecoverable = True
                print(line)
            else:
                s = re.search('FAIL\s+(github.com.*)\s[\d\.]+s\s*$', line)
                db['failures'][s.group(1)] = re_run_tests
                re_run.append({
                    'package': s.group(1),
                    'tests': re_run_tests,
                })
                re_run_tests = []

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

                if name_search and len(tests):
                    runner = os.path.join(name_search.group(1), 'testJujuRunner')
                    run('go test -c -i -o {} {}'.format(runner, package))

                    for test in tests:
                        out, rc = run('./{} -check.f ^{}$'.format(runner, test), write_to=f, fail_ok=True)

                        if args.stop_on_failure and rc:
                            os.remove(runner)
                            return rc

                        failed = failed or rc != 0
                        if rc:
                            failures.append(test)

                    os.remove(runner)

                if len(failures):
                    db['failures'][package] = failures
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

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--rerun', action='store_true')
    parser.add_argument('--changed', action='store_true')
    parser.add_argument('--stop-on-failure', action='store_true')
    args = parser.parse_args()

    # We store test results in a JSON blob.
    db_filename = os.path.join(os.path.expanduser('~'), '.jujutest.json')
    if os.path.exists(db_filename):
        with open(db_filename) as f:
            db = json.load(f)
    else:
        db = {'failures': {}}

    rc = main(args, db)
    with open(db_filename, 'w') as f:
        json.dump(db, f, sort_keys=True, indent=4)

    exit(rc)
