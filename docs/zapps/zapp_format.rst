.. _zapp_format:

ZApp format description
=======================

This document refers to version 2 of the Zoe application description format.

A Zoe application description is a JSON document. Currently we generate them via a set of python scripts available in the `zoe-applications <https://github.com/DistributedSystemsGroup/zoe-applications>`_ repository, but nothing prevents you generating JSON in some other way, obeying the format described here.

At the top level map there are some settings, mostly metadata, and a list of services. Each service has its own metadata and some docker-related parameters.

Top level
---------

A ZApp is completely contained in a JSON Object.

name
^^^^

required, string

The name of this Zapp. Do not confuse this with the name of the execution: you can have many executions (experiment-1, experiment-2) of the same ZApp.

version
^^^^^^^

required, number

The ZApp format version of this description. Zoe will check this value before trying to parse the rest of the ZApp to make sure it is able to correctly interpret the description.

will_end
^^^^^^^^

required, boolean

Must be set to False if potentially this application could run forever. For example a Jupyter notebook will never end (must be terminated explicitly by the user), so needs to have this value set to ``false``. A Spark job instead will finish by itself, so for batch ZApps set this value to ``true``.

priority
^^^^^^^^

required, number [0, 1024)

For now this value is unused.

disable_autorestart
^^^^^^^^^^^^^^^^^^^

optional, boolean

If set to true, disables all kinds of auorestart on all services of this ZApp.

requires_binary
^^^^^^^^^^^^^^^

required, boolean

For now this value is unused.

services
^^^^^^^^

required, array

The list of services to include in this ZApp.

Services
--------

Each service is a JSON Object. At least one service needs to have the monitor key set to ``true``, see its description below form more details.

name
^^^^

required, string

The name of this service. This value will be combined with other information to generate the unique network names that can be used by services to talk to each other.

environment
^^^^^^^^^^^

required, array

Environment variables to be passed to the service/container. Each entry in the array must be an array with two elements, the variable name and its value.

A number of special values can be used, these will be substituted by Zoe when the ZApp is executed.

* ``{user_name}`` : the Zoe user name of the user execution the ZApp
* ``{execution_id}`` : the unique identified for this execution
* ``{execution_name}`` : the name given by the user to this execution
* ``{deployment_name}`` : the name of the Zoe deployment
* ``{dns_name#self}`` : the DNS name for this service itself
* ``{dns_name#<service_name_with_counter>}`` : the DNS name of another service defined in the same ZApp. For example, ``{dns_name#jupyter0}`` will be substituted with the DNS name of the first instance of the Jupyter service,

networks
^^^^^^^^

optional, array

A list of additional Docker network IDs to connect to this service. By default only the network configured in Zoe configuration file will be connected.

volumes
^^^^^^^

optional, array

A list of additional volumes to be mounted in this service container. Each volume is described by an array with three elements:

* host path: the path on the host to mounted
* container path: the path inside the container where host path should be mounted
* read only: a boolean, if true the mountpoint will be read only

Zoe will always mount the user workspace directory in ``$ZOE_WORKSPACE``.

docker_image
^^^^^^^^^^^^

required, string

The full name of the Docker image for this service. The registry can be local, but also images on the Docker Hub will work as expected.

monitor
^^^^^^^

required, boolean

If set to ``true``, Zoe will monitor this service for termination. When it terminates, Zoe will proceed killing all the other services of the same execution and set the execution status to ``termianted``.
If set to ``false``, Zoe will configure Docker to automatically restart the service in case it crashes.

Please note that at least one service must be set as a monitor for each ZApp.

All autorestart behaviour is disabled if the global parameter ``disable_autorestart`` (see above) is enabled.

total_count
^^^^^^^^^^^

required, number

The maximum number of services of this type (with the same docker image and associated options) that can be started by Zoe.

essential_count
^^^^^^^^^^^^^^^

required, number <= total_count

The minimum number of services of this type that Zoe must start before being able to consider the ZApp as started. For example, in Spark you need just one worker to produce useful work (essential_count equal to 1), but if there is the possibility of adding up to 9 more workers, the application will run faster (total_count equal to 10).

required_resources
^^^^^^^^^^^^^^^^^^

required, object

Resources that need to be reserved for this service. Currently only ``memory`` is supported, specified in bytes.

startup_order
^^^^^^^^^^^^^

required, number

Relative ordering for service startup. Zoe will start first services with a lower value. Note that Zoe will not wait for the service to be up and running before starting the next in the list.

ports
^^^^^

required, array

A list of ports that the user may wants to access. Currently this is tailored for web interfaces, URLs for each port will be shown in the client interfaces. See the *port* section below for details.

Ports
-----

name
^^^^

required, string

A user friendly description for the service exposed on this port.

path
^^^^

optional, string

The path part of the URL, after the port number. Must start with '/'.

protocol
^^^^^^^^

required, string

The URL protocol

is_main_endpoint
^^^^^^^^^^^^^^^^

required, boolean

Used to emphasize certain service endpoints in the user interface.

expose
^^^^^^

optional, boolean

Expose this port on a public IP address vie Docker. This feature in incomplete: it works only on TCP port and Zoe will not show anywhere the public IP address, that will be available only by using Docker tools.

port_number
^^^^^^^^^^^

required, number

The port number where this service endpoint is exposed.

Example
-------
.. code-block:: json

    {
        "name": "Jupyter notebook",
        "version": 2,
        "will_end": false,
        "priority": 512,
        "requires_binary": false,
        "services": [
            {
                "name": "jupyter",
                "environment": [
                    ["NB_USER", "{user_name}"]
                ],
                "networks": [],
                "docker_image": "docker-registry:5000/apps/jupyter-notebook",
                "monitor": true,
                "total_count": 1,
                "essential_count": 1,
                "required_resources": {
                   "memory": 4294967296
                },
                "startup_order": 0,
                "ports": [
                    {
                        "name": "Jupyter Notebook interface",
                        "path": "/",
                        "protocol": "http",
                        "is_main_endpoint": true,
                        "expose": true,
                        "port_number": 8888
                    }
                ]
            }
        ]
    }
