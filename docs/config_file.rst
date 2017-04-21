.. _config_file:

Zoe configuration
=================

Zoe can be configured by files, environment variables or commandline options. The configuration directives listed in this file can be specified by any of the three methods. Use the ``--help`` command-line option to have more details on the format od environment variables and precedence rules.

Also the directive ``--write-config <filename>`` is available: it will generate a configuration file with all options set to the default values.

The Zoe config file have a simple format of ``<option name> = <value>``. Dash characters can be use for comments.
All Zoe processes use one single configuration file, called zoe.conf. It is searched in the current working directory and in ``/etc/zoe/``.

zoe.conf
--------

Common options:

* ``debug = <true|false>`` : enable or disable debug log output
* ``api-listen-uri = tcp://*:4850`` : ZeroMQ server connection string, used for the master listening endpoint
* ``deployment-name = devel`` : name of this Zoe deployment. Can be used to have multiple Zoe deployments using the same Swarm (devel and prod, for example)
* ``workspace-deployment-path`` : path appended to the workspace path to distinguish this deployment. If unspecified is equal to the deployment name
* ``influxdb-dbname = zoe`` : Name of the InfluxDB database to use for storing metrics
* ``influxdb-url = http://localhost:8086`` : URL of the InfluxDB service (ex. )
* ``influxdb-enable = False`` : Enable metric output toward influxDB
* ``gelf-address = udp://1.2.3.4:1234`` : Enable Docker GELF log output to this destination
* ``workspace-base-path = /mnt/zoe-workspaces`` : Base directory where user workspaces will be created. This directory should reside on a shared filesystem visible by all Docker hosts.
* ``overlay-network-name = zoe`` : name of the pre-configured Docker overlay network Zoe should use
* ``backend = Swarm`` : ' Name of the backend to enable and use

Database options:

* ``dbname = zoe`` : DB name
* ``dbuser = zoe`` : DB user
* ``dbpass = zoe`` : DB password
* ``dbhost = localhost`` : DB hostname
* ``dbport = 5432`` : DB port

API options:

* ``listen-address`` : address Zoe will use to listen for incoming connections to the web interface
* ``listen-port`` : port Zoe will use to listen for incoming connections to the web interface
* ``master-url = tcp://127.0.0.1:4850`` : address of the Zoe Master ZeroMQ API
* ``cookie-secret = changeme``: secret used to encrypt cookies

* ``ldap-server-uri = ldap://localhost`` : LDAP server to use for user authentication
* ``ldap-base-dn = ou=something,dc=any,dc=local`` : LDAP base DN for users
* ``ldap-admin-gid = 5000`` : LDAP group ID for admins
* ``ldap-user-gid = 5001`` : LDAP group ID for users
* ``ldap-guest-gid = 5002`` : LDAP group ID for guests

Scheduler options:

* ``scheduler-class = <ZoeSimpleScheduler | ZoeElasticScheduler>`` : Scheduler class to use for scheduling ZApps (default: simple scheduler)
* ``scheduler-policy = <FIFO | SIZE>`` : Scheduler policy to use for scheduling ZApps (default: FIFO)

Default options for the scheduler enable the traditional Zoe scheduler that was already available in the previous releases.

Backend choice:

* ``backend = <Swarm|Kubernetes>`` : cluster back-end to use to run ZApps

Swarm backend options:

* ``backend-swarm-url = zk://zk1:2181,zk2:2181,zk3:2181`` : connection string to the Swarm API endpoint. Can be expressed by a plain http URL or as a zookeeper node list in case Swarm is configured for HA.
* ``backend-swarm-zk-path = /docker`` : ZooKeeper path used by Docker Swarm
* ``backend-swarm-tls-cert = cert.pem`` : Docker TLS certificate file
* ``backend-swarm-tls-key = key.pem`` : Docker TLS private key file
* ``backend-swarm-tls-ca = ca.pem`` : Docker TLS CA certificate file

Kubernetes backend:

* ``kube-config-file = /opt/zoe/kube.conf`` : the configuration file of Kubernetes cluster that zoe works with. Specified if ``backend`` is ``Kubernetes``.

Proxy options:

By default proxy support is disabled. To configure it refer to the :ref:`proxy documentation <proxy>`.
