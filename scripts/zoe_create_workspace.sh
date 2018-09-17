#!/bin/bash

if [ -z $2 -o -z $1 ]; then
    echo "usage: $0 <username> <fs_uid>"
    exit
fi

mkdir /mnt/nfs/zoe-workspaces/prod/$1
chown $2:zoe-users /mnt/nfs/zoe-workspaces/prod/$1
chmod 700 /mnt/nfs/zoe-workspaces/prod/$1
