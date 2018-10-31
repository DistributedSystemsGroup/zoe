.. _logging:

Zoe logs and service output
===========================

Zoe daemons outputs log information on the standard error stream. More verbose output can be enabled by setting the option ``debug`` to ``true``.

The command-line option ``--log-file`` can be used to specify a file where the output should be written.

Service logs
------------

In this section we focus on the output produced by the ZApps and their services.

Companies and users have a wide variety of requirements for this kind of output:

 * It may need to be stored for auditing or research
 * Users need to access it for debugging or to check progress of their executions
 * ZApps may generate a lot of output in a very short time: it may become a lot of data moving around

Because of this in Zoe we decided to leave the maximum freedom to administrators deploying Zoe. By default Zoe does not configure the container back-ends to do anything special with the output of containers, so whatever is configured there is respected by Zoe.

In this case the logs command line, API and web interface will not be operational.

Docker engine integrated log management
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using the Docker Engine back-end Zoe can configure the containers to produce the output in UDP GELF format and send them to a configured destination, via the ``gelf-address`` option. Each messages is enriched with labels to help matching each log line to the ZApp and service that produced it.

GELF is understood by many tools, like Graylog or the `ELK <https://www.elastic.co/products>`_ and it is possible to store the service output in Elasticsearch and make it searchable via Kibana, for example.

Additionally the Zoe master can itself be configured to act as a log collector. This is enabled by setting the option ``gelf-listener`` to the port number specified in ``gelf-address``. In this case the Zoe Master will activate a thread that listens on that UDP port. Logs will be stored in files, in a directory hierarchy built as follows::

    <service-logs-base-path>/<deployment-name>/<execution-id>/<service-name>.txt

In this case the logs command line, API and web interface will work normally.

Please note that the GELF listener implemented in the Zoe Master process is not built to manage high loads of incoming log messages. If the incoming rate is too high, UDP packets (and hence log lines) may be dropped and lost.

There are two ways to show the logs on the web interface:

1. An implementation of log streaming via web sockets
2. the directory tree created above must be exported via HTTP by an external web server that supports the Range header. This choice is due to performance and reliability. The option ``log-url`` must contain the base url where the directory tree is exposed.
