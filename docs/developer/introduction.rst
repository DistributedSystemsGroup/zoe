General design decisions
========================

Zoe uses an internal state class hierarchy, with a checkpoint system for persistence and debug. This has been done because:
* Zoe state is small
* Relations between classes are simple
* SQL adds a big requirement, with problems for redundancy and high availability
* Checkpoints can be reverted to and examined for debug

For now checkpoints are created each time the state changes.

Authentication: HTTP basic auth is used, as it is the simplest reliable mechanism we could think of. It can be easily secured by adding SSL. Server-side ``passlib`` guarantees a reasonably safe storage of salted password hashes.
There advantages and disadvantages to this choice, but for now we wnat to concentrate on different, more core-related features of Zoe.

Synchronous API. The Zoe Scheduler is not multi-thread, all requests to the API are served immediately. Again, this is done to keep the system simple and is by no means a decision set in stone.

Object naming
-------------
Every object in Zoe has a unique name. Zoe uses a notation with a hierarchical structure, left to right, from specific to generic, like the DNS system.

These names are used throughout the API.

A service (one service corresponds to one Docker container) is identified by this name:
<service_name>-<execution_name>-<owner>-<deployment_name>

An execution is identified by:
<execution_name>-<owner>-<deployment_name>

A user is:
<owner>-<deployment_name>

And a Zoe instance is:
<deployment_name>

Where:
* service name: the name of the service as written in the application description
* execution name: name of the execution as passed to the start API call
* owner: user name of the owner of the execution
* deployment name: configured deployment for this Zoe instance

Docker hostnames
^^^^^^^^^^^^^^^^
The names described above are used to generate the names and host names in Docker. User networks are also named in the same way. This, among other things, has advantages when using Swarm commands, because it is easy to distinguish Zoe containers, and for monitoring solutions that take data directly from Swarm, preserving all labels and container names. With Telegraf, InfluxDB and Grafana it is possible to build Zoe dashboards that show resource utilization per-user or per-execution.
