Container logs
==============

By default Zoe does not involve itself with the output from container processes. The logs can be retrieved with the usual Docker command ``docker logs`` while a container is alive and then they are lost forever.

Using the ``gelf-address`` option of the Zoe Master process, Zoe can configure Docker to send the container outputs to an external destination in GELF format. GELF is the richest format supported by Docker and can be ingested by a number of tools such as Graylog and Logstash. When that option is set all containers created by Zoe will send their output (standard output and standard error) to the destination specified.

Docker is instriucted to add all Zoe-defined tags to the GELF messages, so that they can be aggregate by Zoe Application, Zoe user, etc.

Zoe also provides a Zoe Logger process, in case you prefer to use Kafka in your log pipeline. Each container output will be sent to its own topic, that Kafka will conserve for seven days by default. With Kafka you can also monitor the container output in real-time, for example to debug your container images running in Zoe. In this case GELF is converted to syslog-like format for easier handling

The logger process is very small and simple, you can modify it to suit your needs and convert logs in any format to any destination you prefer.
