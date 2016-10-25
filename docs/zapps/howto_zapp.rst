.. _howto_zapp:

How to build a ZApp
===================

This tutorial will help you build a Zoe Application description starting from the building blocks available in the `Zoe Applications repository <https://github.com/DistributedSystemsGroup/zoe-applications>`_. First we will cover some general concepts and then we will make an example application, a Spark cluster with a Jupyter notebook.

To understand this tutorial you need:

* basic programming experience in Python
* a basic understanding of the analytic framework you want to use
* The Zoe Spark and Jupyter images loaded in a Docker Registry (optional, gives better startup performance)

Here we will not cover how to build Zoe Frameworks and Services. Building them requires in-depth knowledge of Dockerfiles and shell scripting that we cannot include in a short entry-level tutorial such as this one.

General concepts
----------------

ZApps are JSON files.

While writing a ZApp by hand is always an option, it is not the easiest or safest one. Instead almost every programming language provides primitives to read and write JSON files very easily.

In this guide we are going to use Python because it is a very easy language to understand and because the library of Zoe Frameworks and Services that we publish is written in Python. This Python code is run offline, outside of Zoe, to produce the ZApp JSON file. It is this JSON file that is submitted to Zoe for execution.

We are planning graphical tools and a packaging system for ZApps, so stay tuned for updates! In the `Zoe Applications repository <https://github.com/DistributedSystemsGroup/zoe-applications>`_ there is already a very simple web interface we use internally for our users.

.. image:: /figures/zapp_structure.png

A ZApp is a tree of nested dictionaries (other languages call them maps or hashmaps). The actual JSON tree is flattened because Zoe does not need to know about Frameworks, it is a logical subdivision that helps the user.

The ZApp format is versioned. Zoe checks the version field as first thing to make sure it can understand the description. This tutorial is based on version 2 of this format.

The Spark + Jupyter ZApp
------------------------

To build our ZApp, we will write a short Python program that imports the Zoe Frameworks we need and generates a customized ZApp, ready to be submitted to Zoe.

What is described below is just one way of doing things, the one we feel it easier to understand.

Step 1 - setup
^^^^^^^^^^^^^^

Fork and clone the `Zoe Applications repository <https://github.com/DistributedSystemsGroup/zoe-applications>`_, this will let you easily stay updated and commit your own applications.

The repository contains::

    applications/ : some pre-made scripts to build ZApps
    frameworks/ : the frameworks we will use to build our own ZApp
    scripts/ : utility scripts
    web/ : a web application to customize pre-made ZApps
    zoe-app-builder.py : the startup script for the web application

To create a new ZApp, create a subdirectory in `applications/`, let's call it `tutorial_zapp`. Inside open a new file in your favourite text editor, called `spark_jupyter.py`::

    $ cd applications/
    $ mkdir tutorial_zapp
    $ cd tutorial_zapp
    $ touch __init__.py  # This way out ZApp can be imported by the app builder
    $ vi spark_jupyter.py

Step 2 - imports
^^^^^^^^^^^^^^^^

First we need json for the final export::

    import json

Then we need to import the frameworks we need::

    import frameworks.spark.spark as spark_framework
    import frameworks.spark.spark_jupyter as spark_jupyter

These Python modules contain functions that return pre-filled dictionaries, feel free to have a look at their code.

Basically we are selecting some building blocks to compose out application:

* `spark_framework` contains definitions for the Spark Master and the Spark Worker services
* `spark_jupyter` contains the definition for a Jupyter service configured with a pyspark engine.

Finally we need to import the function that will fill in a generic ZApp template::

    import applications.app_base

Step 3 - options
^^^^^^^^^^^^^^^^

Set an application name. It is used mainly for the user interface::

    APP_NAME = 'spark-jupyter'

If you are using an internal registry to hold Zoe images, set its address here (please note the final '/')::

    DOCKER_REGISTRY = '192.168.45.252:5000/'

Otherwise you can use the images on the Docker Hub::

    DOCKER_REGISTRY = ''

Set more options, so that they can be easily changed later::

    options = [
        ('master_mem_limit', 512 * (1024**2), 'Spark Master memory limit (bytes)'),
        ('worker_mem_limit', 12 * (1024**3), 'Spark Worker memory limit (bytes)'),
        ('notebook_mem_limit', 4 * (1024**3), 'Notebook memory limit (bytes)'),
        ('worker_cores', 6, 'Cores used by each worker'),
        ('worker_count', 2, 'Number of workers'),
        ('master_image', DOCKER_REGISTRY + 'zoerepo/spark-master', 'Spark Master image'),
        ('worker_image', DOCKER_REGISTRY + 'zoerepo/spark-worker', 'Spark Worker image'),
        ('notebook_image', DOCKER_REGISTRY + zoerepo/spark-jupyter-notebook', 'Jupyter notebook image'),
    ]

Options are listed in this way (a list of tuples) to ease integration in the app builder web interface. Let's examine each one:

* master_mem_limit: reserve 512MB of RAM for the Spark Master
* worker_mem_limit: reserve 12GB of RAM for each Spark Worker
* notebook_mem_limit: reserve 4GB of RAM for the Jupyter notebook
* worker_cores: each Spark worker will use 6 cores for its executor
* worker_count: we want a total of 2 Spark workers
* {master,worker,notebook}_image: Docker image names for the services, prefixed with the registry address configured above

The option names here match the arguments names of the function we are going to define next.

Step 4 - the ZApp
^^^^^^^^^^^^^^^^^

Here we define the main function that generates the ZApp dictionary::

    def gen_app(notebook_mem_limit, master_mem_limit, worker_mem_limit, worker_cores,
                worker_count,
                master_image, worker_image, notebook_image):
        services = [
            spark_framework.spark_master_service(master_mem_limit, master_image),
            spark_framework.spark_worker_service(worker_count, worker_mem_limit, worker_cores, worker_image),
            spark_jupyter.spark_jupyter_notebook_service(notebook_mem_limit, worker_mem_limit, notebook_image)
        ]
        return applications.app_base.fill_app_template(APP_NAME, False, services)

The function `gen_app()` takes as arguments the options defined in the previous step. It uses these arguments for calling the framework functions and fill a list of services. Finally, with the call to `fill_app_template()` we are populating a generic template with our options and services.

Each framework package defines functions that fill in a template. These functions are actually quite simple, but they hide the structure of the Zoe application description format to simplify the creation of ZApps. They are also hiding the complexities of running Spark in Docker containers: network details and configuration options are already defined and setup correctly.

As can be seen in some of the sample applications (have a look at the `eurecom_aml_lab` one, for example) the service descriptions returned by the template functions can be further customized to add environment variables, docker networks, volumes, etc.

Step 5 - putting it all together
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To make the script executable we need a bit of boilerplate code::

    if __name__ == "__main__":
        args = {}
        for opt in options:
            args[opt[0]] = opt[1]
        app_dict = gen_app(**args)
        json.dump(app_dict, sys.stdout, sort_keys=True, indent=4)
        sys.stdout.write('\n')

This code does not need to change, it takes the option list, transforms it into function arguments, calls `gen_app()` defined above, serializes the output dictionary in human-friendly JSON and dumps it on the standard output.

Now you can save and close the file `spark_jupyter.py`. To execute it do::

    $ PYTHONPATH=../.. python ./spark_jupyter.py | tee my_first_zapp.json

The full description is printed on the screen and saved into a file. The ZApp is available for execution in `my_first_zapp.json`.

Concluding remarks
^^^^^^^^^^^^^^^^^^

In this tutorial we created a Python script that generates a Zoe Application. This ZApps describes a Spark cluster with two workers and a Jupyter notebook. The ZApp can also be easily customized, adding more workers for example, without having to deal with any configuration detail.

The building blocks, the Frameworks and the Service templates, together with the Docker images, hide all the complexity of configuring such a distributed system composed of many different moving parts.

With Zoe and ZApps we want to have many different levels of abstraction, to leave the flexibility in the hands of our users. From top to bottom, increasing the degrees of flexibility and complexity we have:

1. the web application builder: very high level, for end users. They can customize a limited number of predefined applications
2. the Python application descriptions: covered in this tutorial, they can be used to create new applications starting from predefined building blocks
3. the Python service and framework descriptions: can be used as a starting point to create new frameworks and services, together with Docker images
4. JSON descriptions: create a compatible JSON description from scratch using your own tools and languages for maximum flexibility

We have a lot of great ideas on how to evolve the ZApp concept, but we are sure you have many more! Any feedback or comment is always welcome, `contact us directly <daniele.venzano@eurecom.fr>`_ or through the `GitHub issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_.
