#!/usr/bin/env python3

# This script is useful to run Zoe without going through the pip install process when developing

from zoe_storage_server.entrypoint import object_server

if __name__ == '__main__':
    object_server()
