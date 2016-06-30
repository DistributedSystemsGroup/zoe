Zoe - Container-based Analytics as a Service
============================================

Zoe uses `Docker Swarm <https://docs.docker.com/swarm/>`_ to run Analytics as a Service applications.

Zoe is fast: it can create a fully-functional Spark cluster of 20 nodes in less than five seconds.

Zoe is easy to use: just a few clicks on a web interface is all that is needed to configure and start a variety of data-intensive applications. Applications are flexible compositions of Frameworks: for example Jupyter and Spark can be composed to form a Zoe application (a ZApp!).

Zoe is open: applications can be described by a JSON file, anything that can run in a Docker container can be run within Zoe (but we concentrate on data intensive applications).

Zoe is smart: not everyone has infinite resources like Amazon or Google, Zoe is built for small clouds, physical or virtual, and is built to maximize the use of available capacity.

Zoe can use a Docker Swarm located anywhere, on Amazon or in your own private cloud, and does not need exclusive access to it, meaning your Swarm could also be running other services: Zoe will not interfere with them. Zoe is meant as a private service, adding data-analytics capabilities to existing, or new, Docker clusters.

The core components of Zoe are application-independent and users are free to create and execute application descriptions for any kind of service combination. Zoe targets analytics services in particular: we offer a number of tested sample ZApps and Frameworks that can be used as starting examples.

To better understand what we mean by "analytic service", here are a few examples:

* Spark
* Zookeeper
* Hadoop (HDFS in particular)
* Cassandra
* Impala
* ... suggestions welcome!

A number of predefined applications for testing and customization can be found at the `zoe-applications <https://github.com/DistributedSystemsGroup/zoe-applications>`_ repository.

Have a look at the :ref:`vision` and at the :ref:`roadmap` to see what we are currently planning and feel free to `contact us <daniele.venzano@eurecom.fr>`_ via email or through the `GitHub issue tracker <https://github.com/issues>`_ to pose questions or suggest ideas and new features.

Contents:

.. toctree::
  :maxdepth: 2

  install
  config_file
  logging
  monitoring
  architecture
  howto_zapp
  vision
  roadmap
  contributing


A note on terminology
---------------------

We are spending a lot of effort to use consistent naming throughout the documentation, the software, the website and all the other resources associated with Zoe. Check the :ref:`architecture` document for the details, but here is a quick reference:

 * Zoe Components: the Zoe processes, the Master, the API and the service monitor
 * Zoe Applications: a composition of Zoe Frameworks, is the highest-level entry in application descriptions that the use submits to Zoe, can be abbreviated in ZApp(s).
 * Zoe Frameworks: a composition of Zoe Services, is used to describe re-usable pieces of Zoe Applications, like a Spark cluster
 * Zoe Services: one to one with a Docker container, describes a single service/process tree running in an isolated container


Contacts
========

`Zoe website <http://zoe-analytics.eu>`_

Zoe is developed as part of the research activities of the `Distributed Systems Group <http://distsysgroup.wordpress.com>`_ at `Eurecom <http://www.eurecom.fr>`_, in
Sophia Antipolis, France.

The main discussion area for issues, questions and feature requests is the `GitHub issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_.
