.. Zoe documentation master file, created by
   sphinx-quickstart on Fri Sep 11 15:11:20 2015.

Zoe - Container-based Analytics as a Service
============================================

Zoe uses `Docker Swarm <https://docs.docker.com/swarm/>`_ to run Analytics as a Service applications.

Zoe can use a Docker Swarm located anywhere, on Amazon or in your own private cloud, and does not need exclusive access to it, meaning
your Swarm could also be running other services: Zoe will not interfere with them. Zoe is meant as a private service, adding data-analytics
capabilities to existing, or new, Docker clusters, maximising the use of already provisioned capacity.

Currently only the `Spark framework <http://spark.apache.org/>`_ is supported, but we are planning inclusion of other frameworks. Have a look at the :ref:`vision` and at the
`roadmap <https://github.com/DistributedSystemsGroup/zoe/blob/master/README.md>`_ to see what we are currently planning and feel free to contact us through the
GitHub issue tracker to pose questions or suggest ideas and new features.

Contents:

.. toctree::
  :maxdepth: 2

  install
  architecture
  vision
  contributing

Contacts
========

Zoe is developed as part of the research activities of the `Distributed Systems Group <http://distsysgroup.wordpress.com>`_ at `Eurecom <http://www.eurecom.fr>`_, in
Sophia Antipolis, France.

The main discussion area for issues, questions and feature requests is the `GitHub issue tracker <https://github.com/DistributedSystemsGroup/zoe/issues>`_.
