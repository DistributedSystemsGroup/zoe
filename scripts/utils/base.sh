ZK_HOSTS="bf1.bigfoot.eurecom.fr:2181,bf5.bigfoot.eurecom.fr:2181,bf11.bigfoot.eurecom.fr"
SWARM=`utils/find_swarm_master.py $ZK_HOSTS`
REGISTRY=10.1.0.1:5000
