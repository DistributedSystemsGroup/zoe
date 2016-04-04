Installing Zoe
==============

Zoe components:

* Master
* Observer
* logger (optional)
* web client
* command-line client

Zoe is written in Python and uses the ``requirements.txt`` file to list the package dependencies needed for all components of Zoe. Not all of them are needed in all cases, for example you need the ``kazoo`` library only if you use Zookeeper to manage Swarm high availability.

Zoe is a young software project and we foresee it being used in places with wildly different requirements in terms of IT organization (what is below Zoe) and user interaction (what is above Zoe). For this reason we are aiming at providing a solid core of features and a number of basic external components that can be easily customized. For example, the Spark idle monitoring feature is useful only in certain environments and it is implemented as an external service, that can be customized of takes as an example to build something different.

There is an experimental configuration file for Docker Compose, if you want to try it. It will run Zoe and its components inside Docker containers. It needs to be customized with the address of your Swarm master, the port mappings and the location of a shared filesystem.

Overview
--------

The applications run by Zoe, usually, expose a number of interfaces (web, rest and others) to the user. Docker Swarm does not provide an easy way to manage this situation, the prt can be statically allocated, by the public IP address is chosen arbitrarily by Swarm and there is no discovery mechanism (DNS) exposed to the outside of Swarm.

To work around this problem Zoe creates a gateway container for each user. The image used for this gateway container is configurable. The default one, downloaded from the Docker hub contains an ssh-based SOCKS proxy that the user must configure in his/her browser to be able to access the services run by Zoe executions.

Zoe requires a shared filesystem, visible from all Docker hosts. Some Zoe Applications (for example spark submit, MPI) require user-provided binaries to run. Zoe creates and maintains for each user a workspace directory on this shared filesystem. The user can access the directory from outside Zoe and put the files required for his/her application. We are evaluating whether to integrate into the Zoe web client some kind of web interface for accessing the workspace directory.

Requirements
------------

Zoe is written in Python 3. Development happens on Python 3.4, but we test also for Python 3.5 on Travis-CI.

To run Zoe you need Docker Swarm and a shared filesystem, mounted on all hosts part of the Swarm. Internally we use CEPH-FS, but NFS is also a valid solution.

Optional:

* A Docker registry containing Zoe images for faster container startup times
* A logging pipeline able to receive GELF-formatted logs, or a Kafka broker

Swarm/Docker
------------

Install Docker and the Swarm container:

* https://docs.docker.com/installation/ubuntulinux/
* https://docs.docker.com/swarm/install-manual/

For testing you can use a Swarm with a single Docker instance located on the same host/VM.

Network configuration
^^^^^^^^^^^^^^^^^^^^^

Docker 1.9/Swarm 1.0 multi-host networking is used in Zoe:

* https://docs.docker.com/engine/userguide/networking/get-started-overlay/

This means that you will also need a key-value store supported by Docker. We use Zookeeper, it is available in Debian and Ubuntu without the need for external package
repositories and is very easy to set up.

Images: Docker Hub Vs local Docker registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Zoe master will run a gateway container for each user. The image for this container is available on the `Docker Hub <https://hub.docker.com/r/zoerepo/>`_ and is generated from the Dockerfile in the ``gateway-image`` directory of the main Zoe repository.

Since the Docker Hub can be slow, we strongly suggest setting up a private registry, containing also the Zoe Service images. Have a look at the `zoe-applications <https://github.com/DistributedSystemsGroup/zoe-applications>`_ repository for examples of Zoe Applications and Services.


Zoe
---

Currently this is the recommended procedure:

1. Clone the zoe repository
2. Install Python package dependencies: ``pip3 install -r requirements.txt``
3. Create new configuration files for the master and the observer (:ref:`config_file`)
4. Setup supervisor to manage Zoe processes: in the ``scripts/supervisor/`` directory you can find the configuration file for
   supervisor. You need to modify the paths to point to where you cloned Zoe and the user (Zoe does not need special privileges).
5. Start running applications using the command-line client! (the web interface will be coming soon)
