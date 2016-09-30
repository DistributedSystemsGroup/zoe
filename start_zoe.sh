#!/bin/bash

echo "The images for this script are not yet available on the Docker Hub"
exit 1

if [ ! `which tmux` ]; then
	echo "This script uses the tmux terminal multiplexer, but it is not available in PATH"
	exit 1
fi

# Address for the Swarm API endpoint
SWARM_ADDRESS="swarm:2380"


sudo docker -H ${SWARM_ADDRESS} run -i -t --rm=true -e ZOE_MASTER_SWARM=${SWARM_ADDRESS} zoerepo/zoe-master
sudo docker -H ${SWARM_ADDRESS} run -i -t --rm=true zoerepo/zoe-client ./zoe-web.py
