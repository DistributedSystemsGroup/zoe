#!/usr/bin/python3

import sys

from kazoo.client import KazooClient

def zookeeper_swarm(zk_server_list, path='/swarm'):
    path = path + '/docker/swarm/leader'
    zk = KazooClient(hosts=zk_server_list)
    zk.start()
    master, stat = zk.get(path)
    zk.stop()
    return master.decode('utf-8')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Provide zookeeper server list")
    print(zookeeper_swarm(sys.argv[1]))

