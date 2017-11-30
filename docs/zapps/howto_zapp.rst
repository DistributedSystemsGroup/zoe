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
  * ``README-devel.md`` : documentation for the ZApp developer (optional)
  * ``README.md`` : documentation for the ZApp user
  * ``zapp.json`` : JSON ZApp description
  * ``manifest.json`` : manifest with high-level information needed for the ZApp shop
  * ``logo.png`` : logo for the ZApp, it will be used in the future ZAppShop

A ZApp is composed by two main elements:

* a container image: the format depends on the container back-end in use, currently Docker is used for Zoe
* a JSON description: the magic ingredient that makes Zoe work

The JSON description contains all the information needed to start the containers that make up the application. Apart from some metadata, it contains a list of ``services``. Each service describes one or more (almost) identical containers. Please note that Zoe does not replicate services for fault tolerance, but to increase parallelism and performance (think in terms of additional Spark workers, for example).

The ZApp format is versioned. Zoe checks the version field as first thing to make sure it can understand the description. This tutorial is based on version 3 of this format.

The Tensorflow ZApp
-------------------

Clone the `Tensorflow ZApp <https://gitlab.eurecom.fr/zoe/zapp-tensorflow>`_ repository.

The ZApp uses the standard Tensorflow image released by google. The image contains Python, the Tensorflow library and a Jupyter Notebook.

The ``tf-google.json`` file contains the JSON description of the ZApp. The format of this file is described in the :ref:`zapp_format` document.

This ZApp has a single service and is a very good example of how to use a pre-existing image on the Docker Hub for execution in Zoe.

The ``image`` field points to an image name that the Zoe back-end is able to understand. Managing Docker images is outside the scope of Zoe: ideally you have in-place, in your cluster, a system that distributes the images on all the nodes for fast ZApp start-up times and that keeps them updated, to make sure new versions with bug fixes are made automatically available. The ``.gitlab.yml`` file contains the GitLab CI description that we use at Eurecom to automatically deploy new versions of the ZApp in our cluster.

The user is also able to override the ``command``: this way the Notebook is not started and the user command is executed instead, effectively transforming the ZApp into a batch one able to run non-interactive scripts.

The ``manifest.json`` file describes the ZApp in terms of the ZApp Shop in the Zoe web interface. It contains the logo and usage instructions file names and options that are presented to the user when she wants to start the ZApp.
The manifest and the ZApp Shop are documented in the :ref:`install` document.
