#!/bin/bash

#Zoe deploy script for ubuntu 16.04

echo "Installing docker engine..."
sudo apt-get install -y apt-transport-https ca-certificates
sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get install -y docker-engine

echo "Installing docker-compose..."
sudo chown -R $(whoami) /usr/local/bin
curl -L "https://github.com/docker/compose/releases/download/1.9.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

echo "Setting up docker swarm..."
echo "Exporting default NIC..."
export DEFAULT_NIC=$(echo `ip -o -4 route show to default | awk '{print $5}'`)
echo "Exporting Ip address variable..."
export HOST_IP=$(echo `ifconfig $DEFAULT_NIC 2>/dev/null|awk '/inet addr:/ {print $2}'|sed 's/addr://'`)
echo "Appending new entry in hosts file..."
echo $HOST_IP zoe | sudo tee --append /etc/hosts > /dev/null

echo "Removing docker.pid/socks..."
sudo rm /var/run/docker.*
sudo rm -r /var/run/docker
echo "Restarting dockerd daemon with new arguments..."
sudo dockerd --cluster-store=consul://zoe:8500 --cluster-advertise=$DEFAULT_NIC:2375 -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock &

sleep 5

echo "Starting consul..."
sudo docker run -itd -p 8500:8500 progrium/consul -server -bootstrap

sleep 5

echo "Starting swarm manager..."
sudo docker run -itd -p 4000:4000 swarm manage -H :4000 --advertise $HOST_IP:4000 consul://$HOST_IP:8500

sleep 5

echo "Starting swarm worker..."
sudo docker run -itd swarm join --addr=$HOST_IP:2375 consul://$HOST_IP:8500

echo "Installing zoe..."

sleep 5

echo "Creating overlay network..."
sudo docker -H :4000 network create --driver overlay my-net

echo "Starting zoe docker-compose..."
export SWARM_URL=$HOST_IP:4000

echo $SWARM_URL

sed -i -e 's/${SWARM_URL}/'$SWARM_URL'/g' docker-compose.yml

sudo docker-compose up -d
