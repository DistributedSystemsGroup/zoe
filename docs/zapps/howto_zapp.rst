.. _howto_zapp:

How to build a ZApp
===================

This tutorial will help you customize a Zoe Application starting from the `PyDataSci ZApp <https://gitlab.eurecom.fr/zoe/pydatasci>`_. At the end of the tutorial you will be able to customize existing ZApps, but you will also have understood the tools and process necessary to build new ZApps from scratch.

To understand this tutorial you need:

* basic programming experience in Python
* knowledge of Dockerfiles and associated build commands

General concepts
----------------

A ZApp repository contains a number of well-known files, that are used to automatise builds.

* ``root``

  * ``<image name>/`` : directory containing Docker image sources (Dockerfiles and associated files)
  * ``README-devel.md`` : documentation for the ZApp developer (optional)
  * ``README.md`` : documentation for the ZApp user
  * ``zapp.json`` : JSON ZApp description
  * ``manifest.json`` : manifest with high-level information needed for the ZApp shop
  * ``logo.png`` : logo for the ZApp, it will be used in the future ZAppShop

A ZApp is composed by two main elements:

* a container image: the format depends on the container back-end in use, currently Docker is used for Zoe
* a JSON description: the magic ingredient that makes Zoe work

The JSON description contains all the information needed to start the containers that make up the application. Apart from some metadata, it contains a list of ``services``. Each service describes one or more containers. Please note that Zoe does not replicate services for fault tolerance, but to increase parallelism and performance (think in terms of additional Spark workers, for example).

The ZApp format is versioned. Zoe checks the version field as first thing to make sure it can understand the description. This tutorial is based on version 3 of this format.

The PyDataSci ZApp
------------------

Clone the `PyDataSci ZApp <https://gitlab.eurecom.fr/zoe/pydaatsci>`_ repository.

The repository actually contains two ZApps, a normal one and a GPU-enabled one. Both contain the same set of libraries, the only difference being in the NVidia drivers and associated libraries.

The ZApps use custom images for Jupyter Notebooks containing many data science related libraries, including Tensorflow and PyTorch.

The ``gen_json.py`` script generates the two JSON descriptions for Zoe. The format of these files is described in the :ref:`zapp_format` document. Each description contains a single service, the one running the Notebook.

In the description, The ``image`` field points to an image name that the Zoe back-end is able to understand. Managing Docker images is outside the scope of Zoe: ideally you have in-place, in your cluster, a system that distributes the images on all the nodes for fast ZApp start-up times and that keeps them updated, to make sure new versions with bug fixes are made automatically available. The ``.gitlab.yml`` file contains the GitLab CI description that we use at Eurecom to automatically deploy new versions of the ZApp in our cluster.

The user is also able to override the ``command``: this way the Notebook is not started and the user command is executed instead, effectively transforming the ZApp into a batch one able to run non-interactive scripts.

The ``manifest.json`` file describes the ZApp in terms of the ZApp Shop in the Zoe web interface. It contains references to the logo file, documentation to show on the web page and user-visible parameters that are presented to the user when she wants to start the ZApp.
The manifest and the ZApp Shop are documented in the :ref:`install` document.

Adding a library
----------------

To add a new library to the PyDataSci ZApps, you need to open the ``Dockerfile`` in each of the two directories (``pydatasci`` and ``pydatasci-gpu``). Always reproduce the changes in the two files to keep the two versions consistent.

In the Dockerfile you will find a list of libraries installed via ``pip`` and below a list of packages installed via ``apt-get install``. Add your library to the right place and save your changes.

To build your image you need to call Docker. Depending on how your Zoe deployment has been done this could be more or less automated. To do it by hand, you need to run the following command::

    docker build -t pydatasci(-gpu):test pydatasci(-gpu)/

The build process needs to have the Zoe base images already built and available in the system. These can be found in `this repository <https://gitlab.eurecom.fr/zoe-apps/base-images>`_.
