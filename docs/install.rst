Installing Zoe
==============

Zoe components:

* Master
* Observer
* logger
* web client
* command-line client

Zoe is written in Python and uses the ``requirements.txt`` file to list the package dependencies needed for all components of Zoe. Not all of them are needed in all cases, for example you need the ``kazoo`` library only if you use Zookeeper to manage Swarm high availability.

Requirements
------------

Zoe is written in Python 3. Development happens on Python 3.4, but we test also for Python 3.5.

* Docker Swarm

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

The images used by Zoe are available on the Docker Hub:

* https://hub.docker.com/r/zoerepo/

Since the Docker Hub can be slow, we strongly suggest setting up a private registry. The ``build_images.sh`` script in the
`zoe-docker-images <https://github.com/DistributedSystemsGroup/zoe-docker-images>`_ repository can help you populate the registry
bypassing the Hub.

The images are quite standard and can be used also without Zoe. Examples on how to do that, are available in the ``scripts/`` directory.


Zoe
---

Currently this is the recommended procedure:

1. Clone the zoe repository
2. Install Python package dependencies: ``pip3 install -r requirements.txt``
3. Create new configuration files for the master and the observer (:ref:`config_file`)
4. Setup supervisor to manage Zoe processes: in the ``scripts/supervisor/`` directory you can find the configuration file for
   supervisor. You need to modify the paths to point to where you cloned Zoe and the user (Zoe does not need special privileges).
5. Start running applications using the command-line client! (the web interface will be coming soon)
