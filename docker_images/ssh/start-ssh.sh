#!/bin/sh

ssh-keygen -A

/usr/sbin/sshd -D
