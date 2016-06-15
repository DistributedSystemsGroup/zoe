#!/bin/sh

ssh-keygen -A

/usr/sbin/sshd

if [ ! -f /home/user/.ssh/id_rsa ]; then
	su -c "ssh-keygen -f /home/user/.ssh/id_rsa -N \"\"" user
fi
su -c "cp /home/user/.ssh/id_rsa.pub /home/user/.ssh/authorized_keys" user
su -c "ssh -D 1080 -o \"StrictHostKeyChecking no\" -g -N -v localhost" user

