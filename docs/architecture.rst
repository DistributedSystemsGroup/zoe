Architecture
============

Zoe is composed of:

* zoe: command-line client
* zoe-scheduler: the core daemon that performs application scheduling and talks to Swarm
* zoe-web: the web service
* zoe-observer: listens to events from Swarm and looks for idle resources to free automatically

The command line client and the web interface are the user-facing components of Zoe, while the scheduler and the observer are the back ends.

The Zoe scheduler is the core component of Zoe and communicates with the clients by using a REST API. It manages users, applications and executions.
Users submit *application descriptions* and can ask for their execution. The scheduler keeps track of available resources and execution requests, and applies a
scheduling policy to decide which requests should be satisfied as soon as possible and which ones can be deferred for later.

The scheduler talks to Docker Swarm to create and destroy containers and to read monitoring information used to schedule applications.

Application descriptions
------------------------

Application descriptions are at the core of Zoe. They are likely to evolve in time to include more information that needs to be passed to the scheduler.
Currently they are composed of a set of generic attributes that apply to the whole application and a list of processes. Each process describes
a container that will be started on the Swarm.

The Zoe commandline client is able to load a description from a JSON file and a number of predefined application descriptions can be exported to be modified
and customized.

Any number of process can be put in a Zoe application description. The format supports complex scenarios mixing any kind of software that
can be run in Docker containers.

These descriptions are strictly linked to the docker images used in the process descriptions, as they specify environment variables and commands to be executed. We successfully used third party images, demonstrating the generality of zoe's approach.

You can use the ``zoe.py pre-app-list`` and ``zoe.py pre-app-export`` commands to export a JSON-formatted application description to use as a template.
