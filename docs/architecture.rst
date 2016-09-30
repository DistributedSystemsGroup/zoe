.. _architecture:

Architecture
============

The main Zoe Components are:

* zoe master: the core component that performs application scheduling and talks to Swarm
* zoe api: the Zoe frontend, offering a web interface and a REST API
* zoe: command-line client

The Zoe master is the core component of Zoe and communicates with the clients by using an internal ZeroMQ-based protocol. This protocol is designed to be robust, using the best practices from ZeroMQ documentation. A crash of the Api or of the Master process will not leave the other component inoperable, when the faulted process restarts, work will restart where it was left.

In this architecture we moved all the state bookkeeping out to Postgres database. With Zoe we try very hard not to reinvent the wheel and the internal state system we had in the previous architecture iteration was starting to show its limits.

Users submit *execution requests*, composed by a name and an *application description*. The frontend process (Zoe web) informs the Zoe Master that a new execution request is available for execution.
Inside the Master, a scheduler keeps track of available resources and execution requests, and applies a
scheduling policy to decide which requests should be satisfied as soon as possible and which ones can be deferred for later.

The master also talks to Docker Swarm to create and destroy containers and to read monitoring information used to schedule applications.

Application descriptions
------------------------
Application descriptions are at the core of Zoe. They are likely to evolve in time, to satisfy the needs of new distributed analytic engines. The current version is built around several use cases involving MPI, Spark and Jupyter notebooks.

Application descriptions are composed of a set of generic attributes that apply to the whole Zoe Application (abbreviated in ZApp) and a list of Zoe Frameworks. Each Framework is composed by Zoe Services, that describe actual Docker containers. The composition of Frameworks and Services is described by a dependency tree.

The Zoe Service descriptions are strictly linked to the Docker images they use, as they specify environment variables and commands to be executed. We successfully used third party images, demonstrating the generality of Zoe's approach, but in general prefer to build our own.

You can have a look to example applications by going to the `zoe-applications <https://github.com/DistributedSystemsGroup/zoe-applications>`_ repository.
