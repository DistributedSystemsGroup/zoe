.. _config_file:

Zoe configuration
=================

Zoe can be configured by files, environment variables or commandline options. Most of the configuration directives listed in this file can be specified by any of the three methods, with some exception outlined below. Use the ``--help`` command-line option to have more details on the format of environment variables and precedence rules.

Command-line options
--------------------

These options can be specified only on the command-line:

* ``--write-config <filename>`` : generate a configuration file with all options set to the default values
* ``--log-file <filename>`` : write the log output to the specified file instead of ``stderr``

zoe.conf
--------

The Zoe config file have a simple format of ``<option name> = <value>``. Dash characters can be use for comments.
All Zoe processes use one single configuration file, called zoe.conf. It is searched in the current working directory and in ``/etc/zoe/``.

Common options:

* ``debug = <true|false>`` : enable or disable debug log output
* ``deployment-name = devel`` : name of this Zoe deployment. Can be used to have multiple Zoe deployments using the same back-end (devel and prod, for example)

Workspaces:

* ``workspace-deployment-path`` : path appended to the ``workspace-base-path`` to distinguish this deployment. If left unspecified it is equal to the deployment name
* ``workspace-base-path = /mnt/zoe-workspaces`` : Base directory where user workspaces will be created. This directory should reside on a shared filesystem visible by all hosts where containers will be run.

Metrics:

* ``influxdb-dbname = zoe`` : Name of the InfluxDB database to use for storing metrics
* ``influxdb-url = http://localhost:8086`` : URL of the InfluxDB service (ex. )
* ``influxdb-enable = False`` : Enable metric output toward influxDB

Service logs (see: :ref:`logging`):

* ``gelf-address`` : Enable Docker GELF log output to a UDP listener (ex. udp://1.2.3.4:7896), works only for the Swarm back-end
* ``gelf-listener = 7896`` : Enable the internal GELF log listener on this port, set to 0 to disable
* ``service-logs-base-path = /var/lib/zoe/service-logs`` : Path where service logs coming from the GELF listener will be stored

PostgresQL database options:

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

Master options:

* ``api-listen-uri = tcp://*:4850`` : ZeroMQ server connection string, used for the master listening endpoint

Authentication:

* ``auth-type = text`` : Authentication type (text or ldap)
* ``auth-file = zoepass.csv`` : Path to the CSV file containing user,pass,role lines for text authentication
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
* ``overlay-network-name = zoe`` : name of the pre-configured Docker overlay network Zoe should use (Swarm backend)

Kubernetes backend:

* ``kube-config-file = /opt/zoe/kube.conf`` : the configuration file of Kubernetes cluster that zoe works with. Specified if ``backend`` is ``Kubernetes``.

Proxy options:

By default proxy support is disabled. To configure it refer to the :ref:`proxy documentation <proxy>`.
