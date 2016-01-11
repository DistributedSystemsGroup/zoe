#!/bin/bash

DOCKER=`which docker`
if [ -z "$DOCKER" ]; then
	echo "Docker is missing"
fi

DOCKER_VERSION=`$DOCKER --version`
if [ z"$DOCKER_VERSION" != z"Docker version 1.8.3, build f4bf5c7" ]; then
	echo "Wrong Docker version, please use 1.8.3"
fi

if ! which pip > /dev/null; then
	if ! dpkg -l | grep -q kazoo; then
		echo "Please install python-kazoo"
	fi
fi

if ! pip freeze | grep -q kazoo; then
	echo "Please install python-kazoo"
fi

if ! route -n | grep -q 192.168.46; then
	echo "Please add routing: sudo route add -net 192.168.46.0/24 dev eth0"
fi

if ! grep -q -e '\<bigfoot.eurecom.fr\>' /etc/resolv.conf; then
	echo "Please add bigfoot.eurecom.fr to the search list in /etc/resolv.conf"
fi

echo "If nothing is printed above this line, all dependencies are ok"

