.. _config_file:

Zoe config files
================

Zoe config files have a simple format of ``<option name> = <value>``. Dash characters can be use for comments.
Each Zoe process has its own configuration file, as described in the following sections:

zoe-scheduler.conf
------------------
* ``debug = <true|false>`` : enable or disable debug log output
* ``swarm = zk://zk1:2181,zk2:2181,zk3:2181`` : connection string to the Swarm API endpoint. Can be expressed by a plain http URL or as a zookeeper node list in case Swarm is configured for HA.
* ``private-registry = <address:port>`` : address of the private registry containing Zoe images
* ``state-dir = /var/lib/zoe`` : Directory where all state and other binaries (execution logs) are saved.
* ``zoeadmin-password = changeme`` : Password for the zoeadmin user
* ``container-name-prefix = devel`` : prefix used by this instance of Zoe for all names generated in Swarm. Can be used to have multiple Zoe deployments using the same Swarm (devel and prod, for example)
* ``listen-address`` : address Zoe will use to listen for incoming connections to the REST API
* ``listen-port`` : port Zoe will use to listen for incoming connections to the REST API


zoe-observer.conf
-----------------
* ``debug = <true|false>`` : enable or disable debug log output
* ``swarm = zk://zk1:2181,zk2:2181,zk3:2181`` : connection string to the Swarm API endpoint. Can be expressed by a plain http URL or as a zookeeper node list in case Swarm is configured for HA.
* ``zoeadmin-password = changeme`` : Password for the zoeadmin user
* ``container-name-prefix = devel`` : prefix used by this instance of Zoe for all names generated in Swarm. Can be used to have multiple Zoe deployments using the same Swarm (devel and prod, for example)
* ``scheduler-url = http://<address:port>`` : address of the Zoe scehduler rest API
* ``spark-activity-timeout = <seconds>`` : number of seconds to wait before an inactive Spark cluster is automatically terminated


zoe-web.conf
------------
* ``zoe-admin-pass = changeme`` : Password for the zoeadmin user
* ``debug = <true|false>`` : enable or disable debug log output
