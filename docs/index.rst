.. _main_index:

Zoe - Container-based Analytics as a Service
============================================

Zoe provides a simple way to provision data analytics applications. It hides the complexities of managing resources, configuring and deploying complex distributed applications on private clouds. Zoe is focused on data analysis applications, such as `Spark <http://spark.apache.org/>`_ or `Tensorflow <https://www.tensorflow.org/>`_. A generic, very flexible application description format lets you easily describe any kind of data analysis application.

Downloading
-----------

Get Zoe from the `GitHub repository <https://github.com/DistributedSystemsGroup/zoe>`_. Stable releases are tagged on the master branch and can be downloaded from the `releases page <https://github.com/DistributedSystemsGroup/zoe/releases>`_.

Zoe is written in Python 3.4+ and requires a number of third-party packages to function. Deployment scripts for the supported back-ends, install and setup instructions are available in the :ref:`installation guide <install>`.

Quick tutorial
--------------

To use the Zoe command-line interface, first of all you have to define three environment variables::

    export ZOE_URL=http://localhost:5000  # address of the zoe-api instance
    export ZOE_USER=joe                   # User name
    export ZOE_PASS=joesecret             # Password

Now you can check that you are up and running with this command::

    ./zoe.py info

It will return some version information, by querying the zoe-api and zoe-master processes.

Zoe applications are passed as JSON files. A few sample ZApps are available in the ``contrib/zoeapps/`` directory. To start a ZApp use the following command::

    ./zoe.py start joe-spark-notebook contrib/zoeapps/eurecom_aml_lab.json

ZApp execution status can be checked this way::

    ./zoe.py exec-ls                  # Lists all executions, past and present
    ./zoe.py exec-get <execution id>  # Inspects an execution

Where ``execution id`` is the ID of the ZApp execution to inspect, taken from the ``exec-ls`` command.


Where to go from here
---------------------

Main documentation
^^^^^^^^^^^^^^^^^^

.. toctree::
  :maxdepth: 1

  install
  zoe_fe
  kube_backend
  config_file
  logging
  monitoring
  proxy

Zoe applications
^^^^^^^^^^^^^^^^

.. toctree::
  :maxdepth: 1

  zapps/classification
  zapps/howto_zapp
  zapps/zapp_format
  zapps/contributing


Development and contributing to the project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
  :maxdepth: 1

  developer/index
  architecture
  quality
  motivations
  vision
  roadmap
  contributing

External resources
^^^^^^^^^^^^^^^^^^

- `Zoe Homepage <http://zoe-analytics.eu>`_
- `Issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_
- `ZApp repository <https://github.com/DistributedSystemsGroup/zoe-applications>`_

Zoe is licensed under the terms of the Apache 2.0 license.
