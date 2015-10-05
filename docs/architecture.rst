Architecture
============

Zoe is composed of:

* zoe: command-line client
* zoe-scheduler: the main daemon that performs application scheduling and talks to Swarm
* zoe-web: the web service
* zoe-object-storage: a bare bone, persistent, HTTP key-value store for binary values used for logs and application binaries

The command line client and the web interface are the user-facing components of Zoe. They deal with users and maintain *application descriptions*.
They also give access to web interfaces, statistics and monitoring information gathered from Docker, Swarm and the Zoe Scheduler.

The Zoe scheduler is the core component of Zoe and communicates with the clients by using an IPC API. It has no knowledge of users: it receives execution requests
with *application descriptions* attached. The scheduler keeps track of running applications and reacts to a number of events, like new application executions or
terminations requests. In the future we are also of scaling executions according to resource pressure or execution deadlines.

The scheduler talks to Docker Swarm to create and destroy containers and to read monitoring information used to schedule applications. It also updates DNS to provide
persistent container naming and service discovery.

Application descriptions
------------------------

Application descriptions are at the core of Zoe. They are likely to evolve in time to include more information that needs to be passed to the scheduler.
Currently they are composed of a set of generic attributes the apply to the whole application and a list of so-called processes. Each process describes
a container that will be started on the Swarm.

Application descriptions are not thought to be written by hand. The Zoe commandline client is able to load a description from a JSON file, but that is
discouraged, in favor of using the descriptions generated via the web interface.

Any number of process can be put in a Zoe application description. The format supports complex scenarios mixing any kind of non-interactive software that
can be run in Docker containers.

Generic attributes
^^^^^^^^^^^^^^^^^^

* application_id: it is used by the scheduler to keep track of which executions are coming from the same application. Data from past execution runs
  can be used to make predictions on future executions, so the ability to track application IDs is important.
* priority: a relative priority is assigned by the clients to each execution. Client-side decisions can be takes to give different users different priorities,
  or each user can set priorities on each execution. The scheduler will use this information both, to pass to Swarm a CPU priority hint and, in case of queuing,
  to place the execution request in the queue.
* version: the schema of application descriptions is versioned. This way Zoe can easily evolve the format.

Per-process attributes
^^^^^^^^^^^^^^^^^^^^^^

Many of the attributes are Docker-specific. In particular there is the name of the Docker image to start and a list of environment variables to set. Minimum
resource requirements are also listed.
