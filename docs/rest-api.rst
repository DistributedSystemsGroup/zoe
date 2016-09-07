.. _rest-api:

Zoe REST API
============

Zoe can be used from the command line or the web interface. For more complex tasks also an API is provided, so that Zoe functionality can be accesses programmatically.

The API is provided by the zoe-api processes, on the same port of the web interface (5001 by default). Every URL of the API contains, after the hostname and port, the path ``/api/<api version>/``. This document describes API version 0.6.

Info endpoint
-------------

This endpoint does not need authentication. It returns general, static, information about the Zoe software. It is meant for checking that the client is able to talk correctly to the API server::

    curl http://bf5:8080/api/0.6/info | json_pp


Will return a JSON document, like this::

    {
        "version" : "0.10.1-beta",
        "deployment_name" : "prod",
        "application_format_version" : 2,
        "api_version" : "0.6"
    }

Where:

* ``version`` is the Zoe version
* ``deployment_name`` is the name configured for this deployment (multiple Zoe deployment can share the same cluster)
* ``application_format_version`` is the version of ZApp format this Zoe is able to understand
* ``api_version`` is the API version supported by this Zoe and should match the one used in the request URL

Execution endpoint
------------------

r'/execution/([0-9]+)', ExecutionAPI, route_args),
tornado.web.url(API_PATH + r'/execution/delete/([0-9]+)', ExecutionDeleteAPI, route_args),
tornado.web.url(API_PATH + r'/execution', ExecutionCollectionAPI, route_args),

Service endpoint
----------------
tornado.web.url(API_PATH + r'/service/([0-9]+)', ServiceAPI, route_args),
tornado.web.url(API_PATH + r'/service/logs/([0-9]+)', ServiceLogsAPI, route_args),

Discovery endpoint
------------------

This endpoint does not need authentication. It returns a list of services that meet the criteria passed in the URL. It can be used as a service discovery mechanism for those ZApps that need to know in advance the list of available services.

Request::

    curl http://bf5:8080/api/0.6/discovery/by_group/<execution_id>/<service_type> | json_pp

Where:

* ``execution_id`` is the numeric ID of the execution we need to query
* ``service_type`` is the service name (as defined in the ZApp) to filter only services of that type

Will return a JSON document, like this::

    {
       "service_type" : "boinc-client",
       "execution_id" : "23015",
       "dns_names" : [
          "boinc-client0-23015-prod"
       ]
    }

Where:

* ``service_type`` is the name of the service as passed in the URL
* ``execution_id`` is the execution ID as passed in the URL
* ``dns_names`` is the list of DNS names for each service instance currently active (only one in the example above)

Statistics endpoint
-------------------

This endpoint does not need authentication. It returns current statistics about the internal Zoe status.

Scheduler
^^^^^^^^^
Request::

    curl http://bf5:8080/api/0.6/statistics/scheduler | json_pp

Will return a JSON document, like this::

    {
       "termination_threads_count" : 0,
       "queue_length" : 0
    }

Where:

* ``termination_threads_count`` is the number of executions that are pending for termination and cleanup
* ``queue_length`` is the number of executions in the queue waiting to be started
