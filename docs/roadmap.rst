.. _roadmap:

Roadmap
=======

We, the main developers of Zoe, are an academic research team. As such we have limited resources and through collaborations with other universities and private companies our aim is to do research and advance the state of the art. Our roadmap reflects this and pushes more on large-scale topics than on specific features.

The first priority for Zoe is to mature a stable and modular architecture on which advanced features can be built. Most of the work that is going into version 0.10.x is related to this point.

Scheduler architectures and resource allocation
-----------------------------------------------

In parallel to classic, stable and well known schedulers (FIFO), we plan to design and implement within Zoe novel approaches to application scheduling and resource allocation. This includes:

* Optimistic, pessimistic, distributed, centralized schedulers
* Distributed or centralized schedulers

Scheduling policies
-------------------

While the FIFO policy is fine for many settings, is it not the most efficient way of managing work that can be done concurrently. Many decades of scheduling literature point in all sorts of directions, some of which can find new applications in analytic systems:

* Appropriate management of batch Vs interactive Vs streaming analytic applications
* Deadline scheduling for streaming frameworks
* Size-based scheduling better utilization and smaller response times

Dynamic resource allocation
---------------------------

Users are usually bad guessers on how many resources a particular application will need. We all have a tendency of overestimating resource reservations to make sure there is some headroom for unplanned spikes. This overestimation causes low utilization and non-efficient resource usage: with better reservation and allocation mechanisms that can adapt at runtime, more work could be done with the same resources.

* Resize dynamically running applications in terms of number of services
* Resize dynamically running applications in terms of memory and cores allocated for each service

Fault tolerance
---------------

Any modern system must be able to cope with faults and failures of any kind. Zoe is currently built around state of the art mechanisms for fault tolerance, but this does not stop us from further investigating fault tolerance mechanisms both for Zoe itself and for the applications it runs.
