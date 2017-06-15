.. _scheduler:

The elastic scheduler
=====================

The elastic scheduler, available since the 2016.03 release, is able to use the information about elastic services encoded in ZApp descriptions to make efficient use of the available resources. The algorithm, along with a performance evaluation, is described in detail in this paper: `Flexible Scheduling of Distributed Analytic Applications <https://arxiv.org/abs/1611.09528>`_.

Scheduler classes
=================

.. autoclass:: zoe_master.scheduler.ZoeBaseScheduler
   :members:
