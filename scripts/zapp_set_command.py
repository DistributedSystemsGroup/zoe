#!/usr/bin/python3

"""
Set the command to execute inside a ZApp.
"""

import json
import sys

if len(sys.argv) < 2:
    sys.stderr.write("Missing command line\n")
    sys.exit(1)

zapp = json.load(sys.stdin)

for service in zapp['services']:
    if service['monitor']:
        service['command'] = sys.argv[1]
        break

json.dump(zapp, sys.stdout)
