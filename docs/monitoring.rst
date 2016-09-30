.. _monitoring:

Monitoring interface
====================

Zoe has a built-in metrics generator able to send data to InfluxDB. By default it is disabled, it can be enabled by using the ``influxdb-*`` options available in the master configuration file. Metrics are generated for a number of internal events, listed below, and can be used to monitor Zoe performance and aliveness.

Please note that Zoe does not involve itself with container metrics, to gather container statistics you need to use third party tools able to talk directly to Docker. For example Telegraf, from InfluxData, is able to retain all the label associated with a container, thus producing very useful per-container metrics.

REST API metrics
----------------

These metrics report the latency measured during all API calls, as seen from the Zoe Master process.

service_time
^^^^^^^^^^^^

Time in milliseconds taken to service a request. The tags associated with the request will add more details:

* action: get, post, delete, ...
* user_id: user identifier of the authenticated user that performed the request
