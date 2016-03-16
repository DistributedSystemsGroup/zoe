.. _config_file:

Zoe config files
================

Zoe config files have a simple format of ``<option name> = <value>``. Dash characters can be use for comments.
Each Zoe component has its own configuration file, as described in the following sections:

zoe-master.conf
---------------
* ``debug = <true|false>`` : enable or disable debug log output
* ``swarm = zk://zk1:2181,zk2:2181,zk3:2181`` : connection string to the Swarm API endpoint. Can be expressed by a plain http URL or as a zookeeper node list in case Swarm is configured for HA.
* ``private-registry = <address:port>`` : address of the private registry containing Zoe images
* ``state-dir = /var/lib/zoe`` : Directory where all state and other binaries (execution logs) are saved.
* ``zoeadmin-password = changeme`` : Password for the zoeadmin user
* ``deployment-name = devel`` : name of this Zoe deployment. Can be used to have multiple Zoe deployments using the same Swarm (devel and prod, for example)
* ``listen-address`` : address Zoe will use to listen for incoming connections to the REST API
* ``listen-port`` : port Zoe will use to listen for incoming connections to the REST API
* ``influxdb-dbname = zoe`` : Name of the InfluxDB database to use for storing metrics
* ``influxdb-url = http://localhost:8086`` : URL of the InfluxDB service (ex. )
* ``influxdb-enable = False`` : Enable metric output toward influxDB
* ``passlib-rounds = 60000`` : Number of hashing rounds for passwords, has a sever performance impact on each API call
* ``gelf-address = udp://1.2.3.4:1234`` : Enable Docker GELF log output to this destination


zoe-observer.conf
-----------------
* ``debug = <true|false>`` : enable or disable debug log output
* ``swarm = zk://zk1:2181,zk2:2181,zk3:2181`` : connection string to the Swarm API endpoint. Can be expressed by a plain http URL or as a zookeeper node list in case Swarm is configured for HA.
* ``zoeadmin-password = changeme`` : Password for the zoeadmin user
* ``deployment-name = devel`` : name of this Zoe deployment. Can be used to have multiple Zoe deployments using the same Swarm (devel and prod, for example)
* ``master-url = http://<address:port>`` : address of the Zoe Master REST API
* ``spark-activity-timeout = <seconds>`` : number of seconds to wait before an inactive Spark cluster is automatically terminated, this is done only for guest users
* ``loop-time = 300`` : time in seconds between successive checks for idle applications that can be automatically terminated

zoe-web.conf
------------
* ``debug = <true|false>`` : enable or disable debug log output
* ``zoeadmin-password = changeme`` : Password for the zoeadmin user
* ``listen-address`` : address Zoe will use to listen for incoming connections to the web interface
* ``listen-port`` : port Zoe will use to listen for incoming connections to the web interface
* ``master-url = http://<address:port>`` : address of the Zoe Master REST API


zoe-logger.conf
---------------
This component is optional.

* ``debug = <true|false>`` : enable or disable debug log output
* ``deployment-name = devel`` : name of this Zoe deployment. Can be used to have multiple Zoe deployments using the same Swarm (devel and prod, for example)
* ``influxdb-dbname = zoe`` : Name of the InfluxDB database to use for storing metrics
* ``influxdb-url = http://localhost:8086`` : URL of the InfluxDB service (ex. )
* ``influxdb-enable = False`` : Enable metric output toward influxDB
* ``kafka-broker = 1.2.3.4:9092``: Address of the Kafka broker to send logs to
