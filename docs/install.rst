Installing Zoe
==============

Zoe components:

* scheduler
* observer
* web client
* command-line client

Zoe is written in Python and uses the ``resource.txt`` file to list library dependencies.

Requirements
------------

* Docker Swarm

Optional:

* A Docker registry containing Zoe images for faster container startup times

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

Images: Docker Hub Vs local Docker registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The images used by Zoe are available on the Docker Hub:

* https://hub.docker.com/r/zoerepo/

Since the Docker Hub can be quite slow, we strongly suggest setting up a private registry. The ``build_images.sh`` script in the
`zoe-docker-images <https://github.com/DistributedSystemsGroup/zoe-docker-images>`_ repository can help you populate the registry
bypassing the Hub.

The images are quite standard and can be used also without Zoe. Examples on how to do that, are available in the ``scripts/`` directory.


Zoe
---

Currently this is the recommended procedure:

1. Clone the zoe-scheduler repository
2. Create new configuration files for the scheduler and the observer (:ref:`config_file`)
3. Setup supervisor to manage Zoe processes: in the ``scripts/supervisor/`` directory you can find the configuration file for
   supervisor. You need to modify the paths to point to where you cloned Zoe and the user (Zoe does not need special privileges).
4. Clone the zoe-client repository
5. Start running applications using the command-line client! (the web interface will be coming soon)
