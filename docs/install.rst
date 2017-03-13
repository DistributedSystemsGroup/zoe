.. _install:

Installing Zoe
==============

Zoe components:

* Master
* API
* command-line client
* Service monitor (not yet implemented)

Zoe is written in Python and uses the ``requirements.txt`` file to list the package dependencies needed for all components of Zoe. Not all of them are needed in all cases, for example you need the ``kazoo`` library only if you use Zookeeper to manage Swarm high availability.

Zoe is a young software project and we foresee it being used in places with wildly different requirements in terms of IT organization (what is below Zoe) and user interaction (what is above Zoe). For this reason we are aiming at providing a solid core of features and a number of basic external components that can be easily customized. For example, user management is delegated as much as possible to external services. For now we support LDAP, but other authentication methods can be easily implemented.

There is an experimental configuration file for Docker Compose, if you want to try it. It will run Zoe and its components inside Docker containers. It needs to be customized with the address of your Swarm master, the port mappings and the location of a shared filesystem.

Overview
--------

ZApps, usually, expose a number of interfaces (web, REST and others) to the user. Docker Swarm does not provide an easy way to manage this situation: the port can be statically allocated, but the IP address is chosen arbitrarily by Swarm and there is no discovery mechanism (DNS) exposed to the outside of Swarm.

In the interest of keeping dependencies few and easy to manage, we do not rely on external plugins for networking of volumes.
With the functionality that is built-in into Docker and Swarm there is no good, automated, way to solve the problem of accessing services running inside an overlay network from outside. We decided to leave the network configuration entirely in the hands of who is in charge of doing the deployment: Zoe expects a Docker network name and will connect all containers on that network. How that network is configured is outside Zoe's competence area.

As an example of a simple, robust configuration, we use a standard Swarm configuration, with private and closed overlay networks. We create one overlay network for use by Zoe and spawn two containers attached to it: one is a SOCKS proxy and the other is an SSH gateway. Thanks to LDAP users can use the SSH gateway to create tunnels and copy files from/to their workspace.
These gateway containers are maintained outside of Zoe, at this Github repository: https://github.com/DistributedSystemsGroup/gateway-containers

Zoe requires a shared filesystem, visible from all Docker hosts. Each user has a workspace directory visible from all its running ZApps. The workspace is used to save Jupyter notebooks, copy data from/to HDFS, provide binaries to MPI and Spark applications. Again, there are several plugins for Docker that offer a variety of volume backends: we have chosen the simplest deployment option, by using a shared filesystem mounted on all the hosts to provide workspaces.

Requirements
------------

* Python 3. Development happens on Python 3.4, but we test also for Python 3.5 on Travis-CI.
* Docker Swarm (we have not yet tested the new distributed swarm-in-docker available in Docker 1.12)
* A shared filesystem, mounted on all hosts part of the Swarm. Internally we use CEPH-FS, but NFS is also a valid solution.

Optional:

* A Docker registry containing Zoe images for faster container startup times
* A logging pipeline able to receive GELF-formatted logs, or a Kafka broker

Swarm/Docker
------------

Install Docker and the Swarm container:

* https://docs.docker.com/installation/ubuntulinux/
* https://docs.docker.com/swarm/install-manual/

Network configuration
^^^^^^^^^^^^^^^^^^^^^

Docker 1.9/Swarm 1.0 multi-host networking can be used in Zoe:

* https://docs.docker.com/engine/userguide/networking/get-started-overlay/

This means that you will also need a key-value store supported by Docker. We use Zookeeper, it is available in Debian and Ubuntu without the need for external package repositories and is very easy to set up.

Images: Docker Hub Vs local Docker registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A few sample ZApps have their images available on the Docker Hub. We strongly suggest setting up a private registry, containing your customized Zoe Service images. Have a look at the `zoe-applications <https://github.com/DistributedSystemsGroup/zoe-applications>`_ repository for examples of Zoe Applications and Services that can be customized, built and loaded on the Hub or on a local registry.

Zoe
---

Currently this is the recommended procedure, once the initial Swarm setup has been done:

1. Clone the zoe repository
2. Install Python package dependencies: ``pip3 install -r requirements.txt``
3. Create new configuration files for the master and the api processes (:ref:`config_file`)
4. Setup supervisor to manage Zoe processes: in the ``scripts/supervisor/`` directory you can find the configuration file for
   supervisor. You need to modify the paths to point to where you cloned Zoe and the user (Zoe does not need special privileges).
5. Start running ZApps!

Docker compose - demo install
-----------------------------

In the repository there is also a ``docker-compose.yml`` file that can be used to start a simple Zoe deployment for testing and demonstration purposes. By modifying the compose configuration file and adding volumes with customized configuration files it is possible to run more complex Zoe configurations.

Linux standalone install
------------------------

The following steps describe how to run a minimal workable Zoe on a fresh Ubuntu machine. The current supported OS is Ubuntu 16.04 but it is straightforward to modify to work with other versions.

```
git clone http://github.com/DistributedSystemsGroup/zoe-kpmg.git
```

Go to ``deploy`` folder, then:

```
chmod +x deploy.sh
sudo ./deploy.sh
```
