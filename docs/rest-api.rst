.. _rest-api:

Zoe REST API
============

Zoe can be used from the command line or the web interface. For more complex tasks also an API is provided, so that Zoe functionality can be accesses programmatically.

The API is provided by the zoe-api processes, on the same port of the web interface (5001 by default). Every URL of the API contains, after the hostname and port, the path ``/api/<api version>/``. This document describes API version 0.6.

In case the request causes an error, an appropriate HTTP status code is returned. The reply will also contain a JSON document in this format::

    {
        "message": "missing or wrong authentication information"
    }

With an error message detailing the kind of error that happened.

Some endpoints require credentials for authentication. For now the API uses straightforward HTTP Basic authentication. In case credentials are missing or wrong a 401 status code will be returned.

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

All the endpoints listed in this section require authentication.

Execution details
^^^^^^^^^^^^^^^^^

Request (GET)::

    curl -u 'username:password' http://bf5:8080/api/0.6/execution/<execution_id>

Where:

* ``execution_id`` is the ID of the execution we want to inspect

Will return a JSON document like this::

    {
       "status" : "running",
       "description" : {
          "version" : 2,
          "will_end" : false,
    [...]
       },
       "error_message" : null,
       "time_start" : 1473337160.16264,
       "id" : 25158,
       "user_id" : "venzano",
       "time_end" : null,
       "name" : "boinc-loader",
       "services" : [
          26774
       ],
       "time_submit" : 1473337122.99315
    }

Where:

* ``status`` is the execution status. It can be on of "submitted", "scheduled", "starting", "error", "running", "cleaning up", "terminated"
* ``description`` is the full ZApp description as submitted by the user
* ``error_message`` contains the error message in case ``status`` is equal to error
* ``time_submit`` is the time the execution was submitted to Zoe
* ``time_start`` is the time the execution started, after it was queued in the scheduler
* ``time_end`` is the time the execution finished or was terminated by the user
* ``id`` is the ID of the execution
* ``user_id`` is the identifier of the user who submitted the ZApp for execution
* ``name`` is the name of the execution
* ``services`` is a list of service IDs that can be used to inspect single services

Terminate execution
^^^^^^^^^^^^^^^^^^^
This endpoint terminates a running execution.

Request (DELETE)::

    curl -X DELETE -u 'username:password' http://bf5:8080/api/0.6/execution/<execution_id>

If the request is successful an empty response with status code 200 will be returned.

Delete execution
^^^^^^^^^^^^^^^^
This endpoint deletes an execution from the database, terminating it if it is running.

Request (DELETE)::

    curl -u 'username:password' http://bf5:8080/api/0.6/execution/delete/<execution_id>

If the request is successful an empty response with status code 200 will be returned.

List all executions
^^^^^^^^^^^^^^^^^^^

This endpoint will list all executions belonging to the calling user. If the user has an administrator role, executions for all users will be returned.

Request (GET)::

    curl -u 'username:password' http://bf5:8080/api/0.6/execution

Will return a JSON document like this::

    {
       "25152" : {
          "time_submit" : 1473337122.87461,
          "id" : 25152,
    [...]
          "status" : "running",
          "time_start" : 1473337156.8096,
          "services" : [
             26768
          ],
          "time_end" : null,
          "name" : "boinc-loader",
          "error_message" : null
       },
       "25086" : {
          "time_start" : 1473337123.30892,
          "status" : "running",
          "user_id" : "venzano",
    [..]

It is a map with the execution IDs as keys and the full execution details as values.

Start execution
^^^^^^^^^^^^^^^

Request (POST)::

    curl -X POST -u 'username:password' http://bf5:8080/api/0.6/execution



Service endpoint
----------------

All the endpoints listed in this section require authentication.

Service details
^^^^^^^^^^^^^^^

Request::

    curl -u 'username:password' http://bf5:8080/api/0.6/service/<service_id>

Service standard output and error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Request::

    curl -u 'username:password' http://bf5:8080/api/0.6/service/logs/<service_id>

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
