#!/bin/bash

#Zoe deploy script for Windows
#Require to have Docker Toolbox

echo "SCP new profile for boot2docker"
docker-machine scp profile default:/home/docker/profile
docker-machine ssh default "sudo cp /home/docker/profile /var/lib/boot2docker/"
echo "Restart docker daemon with new profile"
docker-machine ssh default "sudo /etc/init.d/docker restart"

echo "Create and start consul container"
docker-machine ssh default "docker run -itd -p 8500:8500 progrium/consul -server -bootstrap"
echo "Create and start swarm manager container"
docker-machine ssh default "docker run -itd -p 4000:4000 swarm manage -H :4000 --advertise 192.168.99.100:4000 consul://192.168.99.100:8500"
echo "Create and start swarm worker container"
docker-machine ssh default "docker run -itd swarm join --addr=192.168.99.100:2376 consul://192.168.99.100:8500"
echo "Create overlay network for Swarm"
docker-machine ssh default "docker -H :4000 network create --driver overlay my-net"

echo "SCP docker-compose.yml for zoe"
docker-machine scp docker-compose.yml default:/home/docker
echo "Download docker-compose and deploy zoe"
docker-machine ssh default "curl -L https://github.com/docker/compose/releases/download/1.10.1/docker-compose-Linux-x86_64 > docker-compose; chmod +x docker-compose; ./docker-compose up -d"
