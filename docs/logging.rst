.. _logging:

Container logs
==============

By default Zoe does not involve itself with the output from container processes. The logs can be retrieved with the usual Docker command ``docker logs`` while a container is alive, they are lost forever when the container is deleted. This solution however does not scale very well: to examine logs, users need to have access to the docker commandline tools and to the Swarm they are running in.

To setup a more convenient logging solution, Zoe provides the ``gelf-address`` option. With it, Zoe can configure Docker to send the container outputs to an external destination in GELF format. GELF is the richest format supported by Docker and can be ingested by a number of tools such as Graylog and Logstash. When that option is set all containers created by Zoe will send their output (standard output and standard error) to the destination specified. Docker is instructed to add all Zoe-defined tags to the GELF messages, so that they can be aggregated by Zoe execution, Zoe user, etc. A popular logging stack that supports GELF is `ELK <https://www.elastic.co/products>`_.

In our experience, web interfaces like Kibana or Graylog are not useful to the Zoe users: they want to quickly dig through logs of their executions to find an error or an interesting number to correlate to some other number in some other log. The web interfaces (option 1) are slow and cluttered compared to using grep on a text file (option 2).
Which alternative is good for you depends on the usage pattern of your users, your log auditing requirements, etc.

What if you want your logs to go through Kafka
----------------------------------------------

Zoe also provides a Zoe Logger process, in case you prefer to use Kafka in your log pipeline. Each container output will be sent to its own topic, that Kafka will retain for seven days by default. With Kafka you can also monitor the container output in real-time, for example to debug your container images running in Zoe. In this case GELF is converted to syslog-like format for easier handling.

The logger process is very small and simple, you can modify it to suit your needs and convert logs in any format to any destination you prefer. It lives in its own repository, here: https://github.com/DistributedSystemsGroup/zoe-logger

If you are interested in sending container output to Kafka, please make your voice heard at `this Docker issue <https://github.com/docker/docker/issues/21271>`_ for a more production-friendly Docker-Kafka integration.

Please note that the ``zoe-logger`` is more or less a toy and can be used as a starting point to develop a more robust and scalable solution. Also, it is currently unmaintained.
