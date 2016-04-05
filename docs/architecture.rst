.. _architecture:

Architecture
============

The main Zoe Components are:

* zoe master: the core component that performs application scheduling and talks to Swarm
* zoe observer: listens to events from Swarm and looks for idle resources to free automatically
* zoe: command-line client

The command line client is the main user-facing component of Zoe, while the master and the observer are the back ends.

The Zoe master is the core component of Zoe and communicates with the clients by using a REST API. It manages users, applications and executions.
Users submit *application descriptions* for execution. Inside the Master, a scheduler keeps track of available resources and execution requests, and applies a
scheduling policy to decide which requests should be satisfied as soon as possible and which ones can be deferred for later.

The master also talks to Docker Swarm to create and destroy containers and to read monitoring information used to schedule applications.

Application descriptions
------------------------
Application descriptions are at the core of Zoe. They are likely to evolve in time to include more information that needs to be passed to the scheduler.
Currently they are composed of a set of generic attributes that apply to the whole Zoe Application and a list of Zoe Frameworks. Each Framework is composed by Zoe Services, that describe actual Docker containers. The composition of Frameworks and Services is described by a dependency tree.

These descriptions are strictly linked to the docker images used in the process descriptions, as they specify environment variables and commands to be executed. We successfully used third party images, demonstrating the generality of Zoe's approach.

Please note that this documentation refers to the full Zoe Application description that is not yet fully implemented in actual code.

You can have a look to example applications by going to the `zoe-applications <https://github.com/DistributedSystemsGroup/zoe-applications>`_ repository.
