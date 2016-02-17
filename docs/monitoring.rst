.. _monitoring:

Monitoring interface
====================

REST API
--------

service_time
^^^^^^^^^^^^

Time in milliseconds taken to service a request. The tags associated with the request will add more details:

* action: get, post, delete, ...
* object: user, application, container, ...
* user: user name of the authenticated user that performed the request

