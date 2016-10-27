Zoe - Container-based Analytics as a Service
============================================

Zoe is a user facing software that hides the complexities of managing resources, configuring and deploying complex distributed applications on private clouds. The main focus are data analysis applications, such as `Spark <http://spark.apache.org/>`_, but Zoe has a very flexible application description format that lets you easily describe any kind of application.

Zoe uses containerization technology to provide fast startup times and process isolation. A smart scheduler is able to prioritize executions according to several policies, maximising the use of the available capacity and maintaining a queue of executions that are ready to run.

Zoe currently supports Docker Swarm as the container backend. It can be located anywhere, on Amazon or in your own private cloud, and Zoe does not need exclusive access to it, meaning your Swarm could also be running other services: Zoe will not interfere with them. Zoe is meant as a private service, adding data-analytics capabilities to new or existing clusters.

The core components of Zoe are application-independent and users are free to create and execute application descriptions for any kind of service combination. Zoe targets analytics services in particular: we offer a number of tested sample ZApps and Frameworks that can be used as starting examples.

To better understand what we mean by "analytic service", here are a few examples:

* Spark
* Zookeeper
* Hadoop (HDFS in particular)
* Cassandra
* Impala
* ... suggestions welcome!

A number of predefined applications for testing and customization can be found at the `zoe-applications <https://github.com/DistributedSystemsGroup/zoe-applications>`_ repository.

Have a look at the :ref:`vision` and at the :ref:`roadmap` to see what we are currently planning and feel free to `contact us <daniele.venzano@eurecom.fr>`_ via email or through the `GitHub issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_ to pose questions or suggest ideas and new features.

A note on terminology (needs to be updated)
-------------------------------------------

We are spending a lot of effort to use consistent naming throughout the documentation, the software, the website and all the other resources associated with Zoe. Check the :ref:`architecture` document for the details, but here is a quick reference:

 * Zoe Components: the Zoe processes, the Master, the API and the service monitor
 * Zoe Applications: a composition of Zoe Frameworks, is the highest-level entry in application descriptions that the use submits to Zoe, can be abbreviated in ZApp(s).
 * Zoe Frameworks: a composition of Zoe Services, is used to describe re-usable pieces of Zoe Applications, like a Spark cluster
 * Zoe Services: one to one with a Docker container, describes a single service/process tree running in an isolated container

Contents
--------

.. toctree::
  :maxdepth: 2

  install
  config_file
  logging
  monitoring
  architecture
  rest-api
  vision
  motivations
  roadmap

Zoe applications
----------------

:ref:`modindex`

.. toctree::
  :maxdepth: 2

  zapps/classification
  zapps/howto_zapp
  zapps/zapp_format
  zapps/contributing

Developer documentation
-----------------------

:ref:`modindex`

.. toctree::
  :maxdepth: 2

  developer/introduction
  developer/rest-api
  developer/auth
  developer/api-endpoint
  developer/master-api
  developer/scheduler

Contacts
========

`Zoe website <http://zoe-analytics.eu>`_

`Zoe mailing list <http://www.freelists.org/list/zoe>`_

About us
========

Zoe is developed as part of the research activities of the `Distributed Systems Group <http://distsysgroup.wordpress.com>`_ at `Eurecom <http://www.eurecom.fr>`_, in Sophia Antipolis, France.

The main discussion area for issues, questions and feature requests is the `GitHub issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_.
