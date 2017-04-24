.. _zapp_format:

ZApp format description
=======================

This document refers to version 2 of the Zoe application description format.

A Zoe application description is a JSON document. Currently we generate them via a set of python scripts available in the `zoe-applications <https://github.com/DistributedSystemsGroup/zoe-applications>`_ repository, but nothing prevents you generating JSON in some other way, obeying the format described here.

At the top level map there are some settings, mostly metadata, and a list of services. Each service has its own metadata and some docker-related parameters.

All fields are required.

Top level
---------

A ZApp is completely contained in a JSON Object.

name
^^^^

string

The name of this Zapp. Do not confuse this with the name of the execution: you can have many executions (experiment-1, experiment-2) of the same ZApp.

version
^^^^^^^

number

The ZApp format version of this description. Zoe will check this value before trying to parse the rest of the ZApp to make sure it is able to correctly interpret the description.

will_end
^^^^^^^^

boolean

Must be set to False if potentially this application could run forever. For example a Jupyter notebook will never end (must be terminated explicitly by the user), so needs to have this value set to ``false``. A Spark job instead will finish by itself, so for batch ZApps set this value to ``true``.

size
^^^^

number >= 0

This value is used by the Elastic scheduler as an hint to the application size.

services
^^^^^^^^

array

The list of services to include in this ZApp.

Services
--------

Each service is a JSON Object. At least one service needs to have the monitor key set to ``true``, see its description below form more details.

name
^^^^

string

The name of this service. This value will be combined with other information to generate the unique network names that can be used by services to talk to each other.

environment
^^^^^^^^^^^

array

Environment variables to be passed to the service/container. Each entry in the array must be an array with two elements, the variable name and its value.

A number of special values can be used, these will be substituted by Zoe when the ZApp is executed.

* ``{user_name}`` : the Zoe user name of the user execution the ZApp
* ``{execution_id}`` : the unique identified for this execution
* ``{execution_name}`` : the name given by the user to this execution
* ``{deployment_name}`` : the name of the Zoe deployment
* ``{dns_name#self}`` : the DNS name for this service itself
* ``{dns_name#<service_name_with_counter>}`` : the DNS name of another service defined in the same ZApp. For example, ``{dns_name#jupyter0}`` will be substituted with the DNS name of the first instance of the Jupyter service,

volumes
^^^^^^^

array

A list of additional volumes to be mounted in this service container. Each volume is described by an array with three elements:

* host path: the path on the host to mounted
* container path: the path inside the container where host path should be mounted
* read only: a boolean, if true the mountpoint will be read only

Zoe will always mount the user workspace directory in ``$ZOE_WORKSPACE``.

image
^^^^^

string

The full name of the Docker image for this service. The registry can be local, but also images on the Docker Hub will work as expected.

monitor
^^^^^^^

boolean

If set to ``true``, Zoe will monitor this service for termination. When it terminates, Zoe will proceed killing all the other services of the same execution and set the execution status to ``termianted``.
If set to ``false``, Zoe will configure Docker to automatically restart the service in case it crashes.

Please note that at least one service must be set as a monitor for each ZApp.

All autorestart behaviour is disabled if the global parameter ``disable_autorestart`` (see above) is enabled.

total_count
^^^^^^^^^^^

number

The maximum number of services of this type (with the same docker image and associated options) that can be started by Zoe.

essential_count
^^^^^^^^^^^^^^^

number <= total_count

The minimum number of services of this type that Zoe must start before being able to consider the ZApp as started. For example, in Spark you need just one worker to produce useful work (essential_count equal to 1), but if there is the possibility of adding up to 9 more workers, the application will run faster (total_count equal to 10).

resources
^^^^^^^^^

object

Resources that need to be reserved for this service. Each resource is specified as a minimum and a maximum. The application is started if the minimum quantity of resources is available in the systems and it is killed if it passes over the maximum limit. If minimum and maximum limits are specified as ``null``, they will be ignored.

``cores`` and ``memory`` are the resources currently supported.

Support for this feature depends on the scheduler and back-end in use.

startup_order
^^^^^^^^^^^^^

number

Relative ordering for service startup. Zoe will start first services with a lower value. Note that Zoe will not wait for the service to be up and running before starting the next in the list.

ports
^^^^^

array

A list of ports that the user may wants to access. Currently this is tailored for web interfaces, URLs for each port will be shown in the client interfaces. See the *port* section below for details.

Ports
-----

Zoe will instruct the backend to expose ports on public addresses. This is usually done by port forwarding and depends on the capabilities of the configured back-end.

name
^^^^

string

A user friendly description for the service exposed on this port.

url_template
^^^^^^^^^^^^

string

A template for the full URL that will be exposed to the user. Zoe will query the backend at run time to get the public IP address and port combination and substitute the ``{ip_port}`` part.

protocol
^^^^^^^^

string

The protocol, either ``tcp`` or ``udp``.

port_number
^^^^^^^^^^^

number

The port number where the service is listening for connections. The external (user-visible) port number will be chosen by the back-end.

Example
-------
.. code-block:: json

    {
        "name": "Jupyter notebook",
        "version": 3,
        "will_end": false,
        "size": 512,
        "services": [
            {
                "name": "jupyter",
                "environment": [
                    ["NB_USER", "{user_name}"]
                ],
                "image": "docker-registry:5000/apps/jupyter-notebook",
                "monitor": true,
                "total_count": 1,
                "essential_count": 1,
                "resources": {
                    "memory": {
                        "min": 4294967296,
                        "max": 4294967296
                    },
                    "cores": {
                        "min": null,
                        "max": null
                    }
                },
                "startup_order": 0,
                "ports": [
                    {
                        "name": "Jupyter Notebook interface",
                        "url_template": "http://{ip_port}/",
                        "protocol": "tcp",
                        "port_number": 8888
                    }
                ]
            }
        ]
    }
