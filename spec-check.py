#!/usr/bin/python3

import yaml
import importlib


def main():
    name = 'delightful'

    with open('{name}.yaml'.format(name=name)) as f:
        charm_metadata = yaml.load(f)

    with open('{name}-variables.yaml'.format(name=name)) as f:
        charm_variables = yaml.load(f)

    generator = importlib.import_module('{name}-output'.format(name=name))
    print(generator.expected(charm_variables))

if __name__ == '__main__':
    main()
