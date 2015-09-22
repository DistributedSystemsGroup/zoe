Planned features for Zoe
========================

Monitoring
----------
Integrate a monitoring solution: Zoe has access to a lot of valuable data that should be recorded and used for feedback and study. Tha data that can be gathered is of two kinds:
1. Events (users starts an execution, cluster finishes, etc.)
2. Statistics: timeseries data gathered from `docker stats`, from the docker hosts (collectd? influxdb?)

Data should be visible by the users. The difficulty of using Grafana for visualization is that it does not handle well showing graphs from different
time intervals, for example to compare the executions of two Spark jobs.

Storage
-------
Zoe should support creating, listing and selecting inputs and outputs for applications. In particular users should be able to create new HDFS clusters or re-use existing
ones, created by them ot by other users. They should be able to list the contents of these storage cluster and select inputs and outputs.
Zoe Scheduler should try to place containers trying to satisfy data-locality constraints, keeping the data containers and the compute containers "near".

For now we are thinking about HDFS, but Cassandra is also a possibility.
