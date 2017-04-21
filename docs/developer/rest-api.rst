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

    curl http://bf5:8080/api/0.6/info


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

    curl -X POST -u 'username:password' --data-urlencode @filename http://bf5:8080/api/0.6/execution

Needs a JSON document passed as the request body::

    {
        "application": <zapp json>,
        'name': "experiment #33"
    }

Where:

* ``application`` is the full ZApp JSON document, the application description
* ``name`` is the name of the execution provided by the user

Will return a JSON document like this::

    {
        "execution_id": 23441
    }

Where:

* ``execution_id`` is the ID of the new execution just created.

Service endpoint
----------------

All the endpoints listed in this section require authentication.

Service details
^^^^^^^^^^^^^^^

Request::

    curl -u 'username:password' http://bf5:8080/api/0.6/service/<service_id>

Will return a JSON document like this::

    {
       "status" : "active",
       "service_group" : "boinc-client",
       "backend_status" : "started",
       "ip_address" : "10.0.0.94",
       "execution_id" : 25158,
       "name" : "boinc-client0",
       "backend_id" : "d0042c69b54e90327d9287e099304b6c25921d81f639803494ea744445d58430",
       "error_message" : null,
       "id" : 26774,
       "description" : {
          "required_resources" : {
             "memory" : 536870912
          },
    [...]
          "name" : "boinc-client",
          "volumes" : []
       }
    }

Where:

* ``status`` is the service status from Zoe point of view. It can be one of "terminating", "inactive", "active" or "starting"
* ``service_group`` is the name for the service provided in the ZApp description. When the ZApp is unpacked to create the actual containers a single service definition will spawn one or more services with this name in common
* ``backend_status`` is the container status from the point of view of the container backend. Zoe tries her best to keep this value in sync, but the value here can be out of sync by several minutes. It can be one of 'undefined', 'created', 'started', 'dead' or 'destroyed'
* ``ip_address`` is the IP address of the container
* ``execution_id`` is the execution ID this service belongs to
* ``name`` is the name for this service instance, generated from ``service_group``
* ``backend_id`` is the ID used by the backend to identify this container
* ``error_message`` is currently unused
* ``id`` is the ID of this service, should match the one given in the URL
* ``description`` is the service description extracted from the ZApp

Service standard output and error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Request::

    curl -u 'username:password' http://bf5:8080/api/0.6/service/logs/<service_id>

Will stream the service instance output, starting from the time the service started. It will close the connection when the service exits.

Discovery endpoint
------------------

This endpoint does not need authentication. It returns a list of services that meet the criteria passed in the URL. It can be used as a service discovery mechanism for those ZApps that need to know in advance the list of available services.

Request::

    curl http://bf5:8080/api/0.6/discovery/by_group/<execution_id>/<service_type>

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

    curl http://bf5:8080/api/0.6/statistics/scheduler

Will return a JSON document, like this::

    {
       "termination_threads_count" : 0,
       "queue_length" : 0
    }

Where:

* ``termination_threads_count`` is the number of executions that are pending for termination and cleanup
* ``queue_length`` is the number of executions in the queue waiting to be started

OAuth2 endpoint
---------------

This endpoint aims to help users authenticate/authorize via an access token instead of raw username/password. It does need authentication when users require new access token. You can refresh an access token by a refresh token.

Request new access token
^^^^^^^^^^^^^^^^^^^^^^^^

Request::

    curl -u 'username:password' http://bf5:8080/api/0.6/oauth/token -X POST -H 'Content-Type: application/json' -d '{"grant_type": "password"}'

Will return a JSON document, like this::

    {
        "token_type": "Bearer",
        "access_token": "3ddbe9ba-6a21-4e4d-993b-70556390c5d3",
        "refresh_token": "9bab190f-e211-42aa-917e-20ce987e355e",
        "expires_in": 36000
    }

Where:

* ``token_type`` is the type of the token, **Bearer** is used as default
* ``access_token`` is the token used for further authentication/authorization with others api endpoints
* ``refresh_token`` is the token used to get new access token when the current one has expired
* ``expires_in`` is the duration of time (second) when the access_token would be expired

Refresh an access token
^^^^^^^^^^^^^^^^^^^^^^^

Request::

    curl  -H 'Authorization: Bearer 9bab190f-e211-42aa-917e-20ce987e355e' http://bf5:8080/api/0.6/oauth/token -X POST -H 'Content-Type: application/json' -d '{"grant_type": "refresh_token"}'

Will return a JSON document, like this::

    {
        "token_type": "Bearer",
        "access_token": "378f8d5f-2eb5-4181-b632-ad23c4534d32",
        "expires_in": 36000
    }

Where:

* ``access_token`` is the new access token after users issue a refresh

Revoke an access/refresh token
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Request::

    curl -u 'usernam:password' -X DELETE http://bf5:8080/api/0.6/oauth/revoke/<token>

Where:

* ``token`` is the access token or refresh token needs to be revoked

Will return a JSON document, like this::

    {
        "ret": "Revoked token."
    }

Authenticate other api endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Instead of sending raw username, password to request results from other api endpoints which require authentication, use an access token with header ``Authorization: Bearer <token>``

Example::

    curl -H 'Authorization: Bearer 378f8d5f-2eb5-4181-b632-ad23c4534d32' http://bf5:8080/api/0.6/execution

Login endpoint
--------------
Get back a cookie for further authentication/authorization with other api endpoints instead of using raw username, password

Request::

   curl -u 'username:password' -c zoe_cookie.txt http://bf5:8080/api/0.6/login

Will return a JSON document, like this::

    {
        "role": "admin",
        "uid": "admin"
    }

And a file named zoe_cookie.txt contains the cookie information.

Pass this cookie on each api request which requires authentication.

Example::

    curl -b zoe_cookie.txt http://bf5:8080/api/0.6/execution

Note:

- For zoe web interface, we require cookie_based mechanism for authentication/authorization.
- Every unauthorized request will be redirected to **http://bf5:8080/login**
- After successfully login, a cookie will be saved at browser for further authentication/authorization purpose.

