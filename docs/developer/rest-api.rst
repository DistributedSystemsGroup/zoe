.. _rest-api:

Zoe REST API
============

Zoe can be used from the command line or the web interface. For more complex tasks also an API is provided, so that Zoe functionality can be accesses programmatically.

The API is provided by the zoe-api processes, on the same port of the web interface (5001 by default). Every URL of the API contains, after the hostname and port, the path ``/api/<api version>/``. **The current API version is 0.7**.

In case the request causes an error, an appropriate HTTP status code is returned. The reply will also contain a JSON document in this format::

    {
        "message": "missing or wrong authentication information"
    }

With an error message detailing the kind of error that happened.

Some endpoints require credentials for authentication. The API uses HTTP Basic authentication. After the first successful authentication, a cookie will be returned in the response headers. The cookie can be used as an authentication token for the subsequent requests.

Login endpoint
--------------
Get back a cookie for further authentication/authorization with other api endpoints instead of using HTTP basic username, password

Request::

   curl -u 'username:password' -c zoe_cookie.txt http://bf5:8080/api/<api_version>/login

Will return a JSON document, like this::

    {
        "user": {
            "fs_uid": 10000,
            "email": "user@domain",
            "quota_id": 1,
            "auth_source": "pam",
            "role_id": 1,
            "id": 8,
            "priority": 0,
            "username": "user33",
            "enabled": true
        }
    }

And the file named ``zoe_cookie.txt`` contains the cookie information.

Pass this cookie on each api request which requires authentication.

Example::

    curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/execution

Note:

- For zoe web interface, we require cookie_based mechanism for authentication/authorization.
- Every unauthorized request will be redirected to **http://<hostname>:8080/login**
- After a successful login, a cookie will be saved in the browser for further authentication/authorization purpose.

Info endpoint
-------------

This endpoint does not need authentication. It returns general, static, information about the Zoe software. It is meant for checking that the client is able to talk correctly to the API server::

    curl http://bf5:8080/api/<api_version>/info


Will return a JSON document, like this::

    {
        "version" : "2017.12",
        "deployment_name" : "prod",
        "application_format_version" : 3,
        "api_version" : "0.7"
    }

Where:

* ``version`` is the Zoe version
* ``deployment_name`` is the name configured for this deployment (multiple Zoe deployment can share the same cluster)
* ``application_format_version`` is the version of ZApp format this Zoe is able to understand
* ``api_version`` is the API version supported by this Zoe and should match the one used in the request URL

ZApp validation endpoint
------------------------

This endpoint does not need authentication. Use this endpoint to validate ZApp descriptions against the deployed Zoe version.

Usage::

    curl -X POST --data-urlencode @filename http://bf5:8080/api/<api_version>/zapp_validate

The full ZApp JSON document, the application description document, is expected as the body of the request.

Will return a 200 HTTP status in case the JSON document passes validation, 400 otherwise.

Execution endpoint
------------------

All the endpoints listed in this section require authentication.

Execution details
^^^^^^^^^^^^^^^^^

Request (GET)::

    curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/execution/<execution_id>

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
       "user_id" : 1,
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

    curl -X DELETE -b zoe_cookie.txt http://bf5:8080/api/<api_version>/execution/<execution_id>

If the request is successful an empty response with status code 200 will be returned.

Delete execution
^^^^^^^^^^^^^^^^
This endpoint deletes an execution from the database, terminating it if it is running.

Request (DELETE)::

    curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/execution/delete/<execution_id>

If the request is successful an empty response with status code 200 will be returned.

List all executions
^^^^^^^^^^^^^^^^^^^

This endpoint will list all executions belonging to the calling user. If the user has an administrator role, executions for all users will be returned.

Request (GET)::

    curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/execution

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
          "user_id" : 1,
    [..]

It is a map with the execution IDs as keys and the full execution details as values.

Starting from verion 0.7 of the API, the execution list can be filtered.

You need to pass via the URL (GET parameters) the criteria to be used for filtering, for example::

    curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/execution?status=terminated\&limit=1

Valid criteria that can be used are:

* status: one of submitted, scheduled, starting, error, running, cleaning up, terminated
* name: execution mane
* user_id: user_id owning the execution (admin only)
* limit: limit the number of returned entries
* earlier_than_submit: all execution that where submitted earlier than this timestamp
* earlier_than_start: all execution that started earlier than this timestamp
* earlier_than_end: all execution that ended earlier than this timestamp
* later_than_submit: all execution that where submitted later than this timestamp
* later_than_start: all execution that started later than this timestamp
* later_than_end: all execution that started later than this timestamp

All timestamps should be passed as number of seconds since the epoch (UTC timezone).

Start execution
^^^^^^^^^^^^^^^

Request (POST)::

    curl -X POST -b zoe_cookie.txt --data-urlencode @filename http://bf5:8080/api/<api_version>/execution

Needs a JSON document passed as the request body::

    {
        "application": <zapp json>,
        "name": "experiment #33"
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

Execution endpoints
^^^^^^^^^^^^^^^^^^^

Request (GET)::

    curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/execution/endpoints/<execution_id>


Will return a JSON list like this::

    [
        ['Jupyter Notebook interface', 'http://192.168.47.19:32920/'],
        [...]
    ]

Where each item of the list is a tuple containing:

* The endpoint name
* The endpoint URL

Service endpoint
----------------

All the endpoints listed in this section require authentication.

Service details
^^^^^^^^^^^^^^^

Request::

    curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/service/<service_id>

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
    [...]
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

    curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/service/logs/<service_id>

Will stream the service instance output, starting from the time the service started. It will close the connection when the service exits.

Discovery endpoint
------------------

This endpoint does not need authentication. It returns a list of services that meet the criteria passed in the URL. It can be used as a service discovery mechanism for those ZApps that need to know in advance the list of available services.

Request::

    curl http://bf5:8080/api/<api_version>/discovery/by_group/<execution_id>/<service_type>

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

    curl http://bf5:8080/api/<api_version>/statistics/scheduler

Will return a JSON document, like this::

    {
       "termination_threads_count" : 0,
       "queue_length" : 0,
       [...]
    }

Where:

* ``termination_threads_count`` is the number of executions that are pending for termination and cleanup
* ``queue_length`` is the number of executions in the queue waiting to be started

The actual content of the response may vary between different Zoe releases.

User endpoints
--------------

These endpoints modify the user tables in Zoe. For more information about users, check :ref:`users`.

Get from ID
^^^^^^^^^^^

Request::

   curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/user/<user_id>

Will return a JSON document, like this::

    {
        "user": {
            "fs_uid": 10000,
            "email": "user@domain",
            "quota_id": 1,
            "auth_source": "pam",
            "role_id": 1,
            "id": 8,
            "priority": 0,
            "username": "user33",
            "enabled": true
        }
    }

Create
^^^^^^

Request::

    curl -X POST -b zoe_cookie.txt --data-urlencode @filename http://bf5:8080/api/<api_version>/user

Needs a JSON document passed as the request body::

    {
        "username": <new username>,
        "email": <email>,
        "role_id": <ID of an existing role>,
        "quota_id": <ID of an existing quota>,
        "auth_source": <authentication method>
    }

Will return a JSON document like this::

    {
        "user_id": 23
    }

Where:

* ``user_id`` is the ID of the new user just created.

Please note that to set the password a second request to the update user endpoint needs to be performed.

Search
^^^^^^

Request::

     curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/user?username=<username>

The following filters can be used:

* username
* email
* priority
* enabled
* auth_source
* role_id
* quota_id

Will return a JSON document like this::

    {
        "33": {
        ... user object ...
        },
        "44": {
        ... user object ...
        }
    }

Delete
^^^^^^

Request::

    curl -X DELETE -b zoe_cookie.txt http://bf5:8080/api/<api_version>/user/<user_id>

If the request is successful an empty response with status code 200 will be returned.

Update
^^^^^^
Request::

    curl -X POST -b zoe_cookie.txt http://bf5:8080/api/<api_version>/user/<user_id>

Needs a JSON document passed as the request body::

    {
        "username": <new username>,
        "password": <new password>,
        "email": <email>,
        "role_id": <ID of an existing role>,
        "quota_id": <ID of an existing quota>,
        "auth_source": <authentication method>
    }

The document should contain only the fields to update.

Role endpoints
--------------

These endpoints modify the role tables in Zoe. For more information about roles, check :ref:`roles`.

Get from ID
^^^^^^^^^^^

Request::

   curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/role/<role_id>

Will return a JSON document, like this::

    {
        "role": {
            "can_change_config": true,
            "can_delete_executions": true,
            "name": "admin",
            "can_see_status": true,
            "can_access_full_zapp_shop": true,
            "id": 1,
            "can_operate_others": true,
            "can_customize_resources": true,
            "can_access_api": true
        }
    }

Create
^^^^^^

Request::

    curl -X POST -b zoe_cookie.txt --data-urlencode @filename http://bf5:8080/api/<api_version>/role

Needs a JSON document passed as the request body::

    {
        "name": <name of the new role>,
        "can_change_config": <true|false>,
        "can_delete_executions": <true|false>,
        "can_see_status": <true|false>,
        "can_access_full_zapp_shop": <true|false>,
        "can_operate_others": <true|false>,
        "can_customize_resources": <true|false>,
        "can_access_api": <true|false>
    }

Will return a JSON document like this::

    {
        "role_id": 23
    }

Where:

* ``role_id`` is the ID of the new role just created.


Search
^^^^^^

Request::

     curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/role?name=<role name>

The following filters can be used:

* name

Will return a JSON document like this::

    {
        "3": {
        ... role object ...
        },
        "44": {
        ... role object ...
        }
    }

Delete
^^^^^^

Request::

    curl -X DELETE -b zoe_cookie.txt http://bf5:8080/api/<api_version>/role/<role_id>

If the request is successful an empty response with status code 200 will be returned.

Update
^^^^^^

Request::

    curl -X POST -b zoe_cookie.txt @filename http://bf5:8080/api/<api_version>/role/<role_id>

Needs a JSON document passed as the request body::

    {
        "name": <name of the new role>,
        "can_change_config": <true|false>,
        "can_delete_executions": <true|false>,
        "can_see_status": <true|false>,
        "can_access_full_zapp_shop": <true|false>,
        "can_operate_others": <true|false>,
        "can_customize_resources": <true|false>,
        "can_access_api": <true|false>
    }

The document should contain only the fields to update.

Quota endpoints
---------------

These endpoints modify the quota tables in Zoe. For more information about quotas, check :ref:`quotas`.

Get from ID
^^^^^^^^^^^

Request::

   curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/quota/<user_id>

Will return a JSON document, like this::

    {
        "quota": {
            "concurrent_executions": 5,
            "cores": 5,
            "id": 1,
            "name": "default",
            "memory": 34359738368
        }
    }


Create
^^^^^^

Request::

    curl -X POST -b zoe_cookie.txt --data-urlencode @filename http://bf5:8080/api/<api_version>/quota

Needs a JSON document passed as the request body::

    {
        "name": <name of the new quota>,
        "concurrent_executions": <maximum number of running executions>,
        "memory": <maximum amount of memory reserved across all running executions>,
        "cores": <maximum amount of cores reserved across all running executions>
    }

Will return a JSON document like this::

    {
        "quota_id": 23
    }

Where:

* ``quota_id`` is the ID of the new quota just created.

Search
^^^^^^

Request::

     curl -b zoe_cookie.txt http://bf5:8080/api/<api_version>/quota?name=<quota name>

The following filters can be used:

* name

Will return a JSON document like this::

    {
        "3": {
        ... quota object ...
        },
        "44": {
        ... quota object ...
        }
    }

Delete
^^^^^^

Request::

    curl -X DELETE -b zoe_cookie.txt http://bf5:8080/api/<api_version>/quota/<quota_id>

If the request is successful an empty response with status code 200 will be returned.

Update
^^^^^^

Request::

    curl -X POST -b zoe_cookie.txt http://bf5:8080/api/<api_version>/quota/<quota_id>

Needs a JSON document passed as the request body::

    {
        "name": <name of the new quota>,
        "concurrent_executions": <maximum number of running executions>,
        "memory": <maximum amount of memory reserved across all running executions>,
        "cores": <maximum amount of cores reserved across all running executions>
    }

The document should contain only the fields to update.
