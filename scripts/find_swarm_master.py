#!/usr/bin/python3

"""
Find the Swarm manager by querying ZooKeeper.
"""

import sys

from kazoo.client import KazooClient


def zookeeper_swarm(zk_server_list, path='/swarm'):
    """Query ZooKeeper."""
    path += '/docker/swarm/leader'
    zk = KazooClient(hosts=zk_server_list)
    zk.start()
    master, stat_ = zk.get(path)
    zk.stop()
    return master.decode('utf-8')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Provide zookeeper server list")
    print(zookeeper_swarm(sys.argv[1]))

