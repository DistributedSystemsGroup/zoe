Zoe - Container-based Analytics as a Service
============================================

Zoe uses `Docker Swarm <https://docs.docker.com/swarm/>`_ to run Analytics as a Service applications.

Zoe is fast: it can create a fully-functional Spark cluster of 20 nodes in less than five seconds.

Zoe is easy to use: just a few clicks on a web interface is all that is needed to configure and start a variety of data-intensive applications.

Zoe is open: applications can be described by a JSON file, anything that can run in a Docker container can be run within Zoe (but we concentrate on data intensive software)

Zoe is smart: not everyone has infinite resources like Amazon or Google, Zoe is built for small clouds, physical or virtual, and is built to maximize the use of available capacity.

Zoe can use a Docker Swarm located anywhere, on Amazon or in your own private cloud, and does not need exclusive access to it, meaning
your Swarm could also be running other services: Zoe will not interfere with them. Zoe is meant as a private service, adding data-analytics
capabilities to existing, or new, Docker clusters.

The core components of Zoe are application-independent and a user can submit application description for any kind of service combination. Since Zoe targets
analytics services in particular, the client tools offer some pre-configured Zoe applications that can be used as starting examples.

To better understand what we mean by "analytic service", here are a few examples:

* Spark
* Zookeeper
* Hadoop (HDFS in particular)
* Cassandra
* Impala
* ... suggestions welcome!

Have a look at the :ref:`vision` and at the `roadmap <https://github.com/DistributedSystemsGroup/zoe/blob/master/ROADMAP.rst>`_ to see what we are currently
planning and feel free to `contact us <venza@brownhat.org>`_ via email or through the GitHub issue tracker to pose questions or suggest ideas and new features.

Contents:

.. toctree::
  :maxdepth: 2

  install
  config_file
  architecture
  vision
  contributing

Contacts
========

`Zoe website <http://zoe-analytics.eu>`_

Zoe is developed as part of the research activities of the `Distributed Systems Group <http://distsysgroup.wordpress.com>`_ at `Eurecom <http://www.eurecom.fr>`_, in
Sophia Antipolis, France.

The main discussion area for issues, questions and feature requests is the `GitHub issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_.
