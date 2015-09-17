#!/usr/bin/env python3

# This script is useful to run Zoe without going through the pip install process when developing

from zoe_scheduler.entrypoint import zoe_manage

if __name__ == "__main__":
    zoe_manage()
