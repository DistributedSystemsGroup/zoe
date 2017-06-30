.. _howto_zapp:

How to build a ZApp
===================

This tutorial will help you customize a Zoe Application starting from the `Tensorflow ZApp <https://gitlab.eurecom.fr/zoe/zapp-tensorflow>`_. At the end of the tutorial you will be able to customize existing ZApps, but you will also have understood the tools and process necessary to build new ZApps from scratch.

To understand this tutorial you need:

* basic programming experience in Python
* knowledge of Dockerfiles and associated build commands

General concepts
----------------

A ZApp repository contains a number of well-known files, that are used to automatise builds.

* ``root``

  * ``docker/`` : directory containing Docker image sources (Dockerfiles and associated files)
  * ``README-devel.md`` : documentation for the ZApp developer
  * ``README.md`` : documentation for the ZApp user
  * ``build_all.sh`` : builds the Docker images and pushes them to a registry
  * ``gen_*.py`` : Python script that generate the ZApp description JSON files
  * ``logo.png`` : logo for the ZApp, it will be used in the future ZAppShop
  * ``validate_all.sh`` : runs the generated JSON files through the Zoe API validation endpoint

The scripts expect a number of environment variables to be defined:

* DOCKER_REGISTRY : hostname (with port if needed) of the Docker registry to use
* REPOSITORY : name of the image repository inside the registry to use
* VERSION : image version (normally this is set by the CI environment to be a build number or the commit hash)
* VALIDATION_URL : Zoe API URL for the validation endpoint (the default expects the zoe-api process to be running on localhost on the 5001 port)

A ZApp is composed by two main elements:

* a container image: the format depends on the container backend in use, currently Docker is the most common one
* a JSON description: the magic ingredient that makes Zoe work

The JSON description contains all the information needed to start the containers that make up the application. Apart from some metadata, it contains a list of ``services``. Each service describes one or more (almost) identical containers. Please note that Zoe does not replicate services for fault tolerance, but to increase parallelism and performance (think in terms of additional Spark workers, for example).

The ZApp format is versioned. Zoe checks the version field as first thing to make sure it can understand the description. This tutorial is based on version 3 of this format.

The Tensorflow ZApp
-------------------

Clone the `Tensorflow ZApp <https://gitlab.eurecom.fr/zoe/zapp-tensorflow>`_ repository.

It contains two variants of the Tensorflow ZApp that we will examine in detail:

1. A simple ZApp that uses the unmodified Google Docker image with a notebook for interactive use
2. A batch ZApp that uses a custom image containing the HEAD version of Tensorflow


The interactive Tensorflow ZApp with stable release from Google
---------------------------------------------------------------

Open the ``gen_json_google.py`` script.

At the beginning of the file we define two constants:

* APP_NAME : name of Zoe Application. It is used in various places visible to the user.
* ZOE_APPLICATION_DESCRIPTION_VERSION : the format version this description conforms to

Then there is dictionary called ``options`` that lists parameters that can be changed to obtain different behaviors. In this case the ZApp is quite simple and we can tune only the amount of cores and memory that out ZApp is going to consume. This information is going to be used for scheduling and for placing the container in the cluster.

To keep the script standardized other constants are defined here, but are not used in this specific ZApp. They load values from the environment, as defined above.

``GOOG_IMAGE`` contains the name of the container image that Zoe is going to use. Here we point directly to the Tensorflow image on Google's registry.

Services
^^^^^^^^

The first function that is defined in the script is ``goog_tensorflow_service``. It defines the Tensorflow service in Zoe.

The format is detailed in the :ref:`zapp_format` document. Of note, here, are the two network ports that are going to be exposed, one for the Tensorboard interface and one for the Notebook web interface.

The ZApp
^^^^^^^^

At the end an ``app`` dictionary is build, containing ZApp metadata and the service we defined above. The dictionary is then dumped in JSON format, that Zoe can understand.

After running the script, the ZApp can be started with ``zoe.py start google-tensorflow goog_tensorflow.json``

The batch Tensorflow with custom image
--------------------------------------

First of all have a look at the Dockefile contained in ``docker/tensorflow/Dockerfile``.

It is based on a Ubuntu image and installs everything that is needed to build Tensorflow. Since the build system uses bazel, that in turn needs Java, the resulting image is quite large, but it can be used for developing Tensorflow.

It also makes those pesky warnings about Tensorflow not being optimized for your CPU disappear.

The Dockefile clones the Tensorflow repository and build the master branch, HEAD commit.

Please note that there is nothing Zoe-specific in this Dockerfile. Zoe can run pre-built images from public registries as well as custom images from private registries.

Run the ``build_all.sh`` script to build the Docker image. It will take several minutes, so you can have a coffee break in the meantime.

Now open the ``gen_json_standalone.py`` script. It is almost identical to the one we saw above, the only notable change is about the image name, that now is generated from the environment variables used to build the image.

Depending on the backend in use in you Zoe deployment, you may have to pull the image from the registry before being able to start the ZApp.

After running the Python script, the ZApp can be started with ``zoe.py start my-long-running-training custom_tensorflow.json``

Concluding remarks
^^^^^^^^^^^^^^^^^^

In this tutorial we examined in detail a sample Tensorflow ZApp. We saw where the memory and cores parameters are defined and how to customize them.

The tutorial has also explained how to use third party Docker images or how to build new ones in-house for running development versions of standard software.

We have a lot of great ideas on how to evolve the ZApp concept, but we are sure you have many more! Any feedback or comment is always welcome, `contact us directly <daniele.venzano@eurecom.fr>`_ or through the `GitHub issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_.
