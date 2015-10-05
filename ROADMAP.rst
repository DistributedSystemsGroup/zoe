Planned features for Zoe
========================

In-browser terminal
-------------------
When playing on a notebook, it is often useful to have access to a user git account. We don't want necessarily to modify the Notebook web-app, so it would be very nice for a user to open a terminal on the Notebook container (or on the Master container, e.g., for Apache Spark) to pull / push commits to a notebook. Having a link along the list of active applications would do the job.

Monitoring
----------
Integrate a monitoring solution: Zoe has access to a lot of valuable data that should be recorded and used for feedback and study. The data that can be gathered is of two kinds:

1. Events (users starts an execution, cluster finishes, etc.)
2. Statistics: time-series data gathered from `docker stats`, from the docker hosts (collectd? influxdb?)

Data should be visible by the users. The downside of using Grafana for visualization is that it does not handle well showing graphs from different time intervals, for example to compare the executions of two applications (e.g., Spark jobs).

Storage
-------
Zoe should support creating, listing and selecting inputs and outputs data stores for applications (both in interactive and batch modes). In particular, users should be able to create new HDFS clusters or re-use existing ones, created by them ot by other users. They should be able to list the contents of these storage cluster and select inputs and outputs, that their applications will use. For example, it should be straight-forward for a user to find the HDFS cluster containing the input directory or file she wishes to analyze (e.g., with a Spark Application) and cut&paste the relevant access information (host-name or IP address, port, directory) to the command line parameters of their applications or to interactive sessions (like Notebooks).
The Zoe Scheduler should try to place containers trying to satisfy application constraints (e.g., data-locality), keeping the data containers and the compute containers "near" to each other.

For now we are thinking about HDFS, but Cassandra is also a possibility.

Additional Analytics Applications
---------------------------------
Zoe currently supports Apache Spark, but we wish to extend the list of supported Applications. Ultimately, Zoe applications should be designed by its users, so that Zoe must be general enough to accommodate a variety of them, with no need for architectural changes, additional code, or modifications to the user application.

* Add support for Apache Flink
* Add support for Apache Storm
* Add support for Data exploration and BI tools, such as Cloudera Impala
* Add support for additional storage layers: Cloudera Kudu, OpenStack Swift or other object stores

Zoe schedulers
--------------
Focus on two-level scheduling: application scheduler and resource management.

Zoe API
-------
Allow advanced users to build their own scripts locally, and isse Zoe commands through a public API.
