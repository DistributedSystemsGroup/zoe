Installing Zoe
==============

Zoe install procedure is migrating from PIP to Docker containers. The codebase is being split in several components, each will live in its own repository with a Dockerfile
to build the container image.

Requirements
------------

* An SQL database to keep all the state (sqlite is used by default)
* Docker Swarm
* A DNS server for service discovery, with DDNS support

Optional:

* A Docker registry containing Zoe images for Docker image caching

How to install
--------------

First of all make sure you have installed the three requirements listed above.

Database
--------

1. Install MySQL/MariaDB, or any other DB supported by SQLAlchemy.
2. Create a database, a user and a password and use these to build a connection string like ``mysql://<user>:<password>@host/db``

Two different Zoe processes use the database and the config file provides separate options. If you feel the need, you can setup different databases too.

Swarm/Docker
------------

Install Docker and the Swarm container:
* https://docs.docker.com/installation/ubuntulinux/
* https://docs.docker.com/swarm/install-manual/

For testing you can use a Swarm with a single Docker instance located on the same host/VM.

Network configuration
^^^^^^^^^^^^^^^^^^^^^

Zoe assumes that containers placed on different hosts are able to talk to each other freely. Since we use Docker on bare metal, we
use an undocumented network configuration, with the docker bridges connected to a physical interface, so that
containers on different hosts can talk to each other on the same layer 2 domain.
To do that you need also to reset the MAC address of the bridge, otherwise bridges on different hosts will have the same MAC address.

Other configurations are possible, but configuring Docker networking is outside the scope of this document.

Images: Docker Hub Vs local Docker registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The images used by Zoe are available on the Docker Hub:

* https://hub.docker.com/r/zoerepo/

Since the Docker Hub can be quite slow, we strongly suggest setting up a private registry. The ``build_images.sh`` script in the
`zoe-docker-images <https://github.com/DistributedSystemsGroup/zoe-docker-images>`_ repository can help you populate the registry
bypassing the Hub.

The images are quite standard and can be used also without Zoe. Examples on how to do that, are available in the ``scripts/start_cluster.sh`` script.


DNS Server
----------

Setting up a DNS server is not a simple task, but it is a necessary evil. DNS is standard, any service discovery implemented via DNS will work out of the box.
We are currently using Bind as a DNS server internally for all naming needs, Bind is well documented, old, stable and proven, set it up right once and you are done.
If the need arises adding support for other Dynamic DNS update protocols is easy, contact us if you need help.

Zoe
---

Releases are also available through pip: ``pip install zoe-analytics``

For developers, we recommend the following procedure:

1. Clone this repository
2. Generate a sample configuration file with ``zoe.py write-config zoe.conf``
3. Edit ``zoe.conf`` using :ref:`config_file`
4. Create the tables in the database with ``zoe.py --setup-db`` and ``zoe-scheduler.py --setup-db``
5. Setup supervisor to manage Zoe processes: in the ``scripts/supervisor/`` directory you can find the configuration file for
   supervisor. You need to modify the paths to point to where you cloned Zoe and the user (Zoe does not need special privileges).
6. Start running applications! By default Zoe web listens on the 5000 port


Zoe Object Storage
^^^^^^^^^^^^^^^^^^

Application binaries and execution logs are saved in a simple Object Storage server.

* Clone it from git: https://github.com/DistributedSystemsGroup/zoe-object-storage
* Use the Dockerfile to build a Docker image
* Run it
* Put the IP address of the container in Zoe's main configuration file (when the transition to Dockerfiles will be finished it will be possible to use linking instead)