#!/usr/bin/env python
import sys
import yaml


def main():
    fin, fadd, fout = sys.argv[1:4]
    with open(fin, 'r') as f:
        config = yaml.load(f.read(), yaml.SafeLoader)
    with open(fadd, 'r') as f:
        config.update(yaml.load(f.read(), yaml.SafeLoader))
    with open(fout, 'w') as f:
        yaml.dump(config, f)


if __name__ == '__main__':
    sys.exit(main())
