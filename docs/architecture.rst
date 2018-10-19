.. _architecture:

Architecture
============

The main Zoe Components are:

* zoe master: the core component that performs application scheduling and talks to the container back-end
* zoe api: the Zoe frontend, offering a web interface and a REST API
* command-line clients (zoe.py and zoe-admin.py)

The Zoe master is the core component of Zoe and communicates with the clients by using an internal ZeroMQ-based protocol. This protocol is designed to be robust, using the best practices from ZeroMQ documentation. A crash of the Api or of the Master process will not leave the other component inoperable, and when the faulted process restarts, work will restart where it was left.

In this architecture all application state is kept in a Postgres database. Platform state is kept in-memory: built at start time and refreshed periodically. A lot of care and tuning has been spent in keeping synchronized the view Zoe has of the system and the real back-end state. In a few cases containers may be left orphaned: when Zoe deems it safe, they will be automatically cleaned-up, otherwise a warning in the logs will generated and the administrator has to examine the situation as, usually, it points to a bug hidden somewhere in the back-end code.

Users submit *execution requests*, composed by a name and an *application description*. The frontend process (Zoe api) informs the Zoe Master that a new execution request is available for execution.
Inside the Master, a scheduler keeps track of available resources and execution requests, and applies a
scheduling policy to decide which requests should be satisfied as soon as possible and which ones can be deferred for later.

The master also talks to a container orchestrator (Docker for example) to create and destroy containers and to read monitoring information used to schedule applications.

Application descriptions
------------------------
Application descriptions are at the core of Zoe. They are likely to evolve in time, to satisfy the needs of new distributed analytic engines. The current version is built around several use cases involving MPI, Spark and Jupyter notebooks.

Application descriptions are composed of a set of generic attributes that apply to the whole Zoe Application (abbreviated in ZApp) and a list of services. Zoe Services describe actual Docker containers.

The Zoe Service descriptions are strictly linked to the Docker images they use, as they specify environment variables and commands to be executed. We successfully used unmodified third party images, demonstrating the generality of Zoe's approach.
