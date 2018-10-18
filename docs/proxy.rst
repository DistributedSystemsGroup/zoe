.. _proxy:

Accessing Zoe through a reverse proxy
=====================================

The Zoe web interface and REST API can be exposed through a reverse proxy. Additionally some support for exposing the web interfaces of running executions is also available, with some constraints.

Configuration
-------------

* reverse-proxy-path : path-portion of the external URL in case Zoe is exposed by the reverse proxy under a path (ex.: /zoe)
* websocket_base : Base URL for websocket connections (ex.: ws://<server_address>)

Accessing ZApps through the Træfik reverse proxy
------------------------------------------------

Zoe contains support for dynamically updating a reverse proxy for giving access to users without exposing internal IP addresses. This support is experimental and comes with several limitations:

* Only web interfaces can be exposed via a reverse proxy
* Only Træfik with a ZooKeeper dynamic configuration backend is supported
* Usually the web application running in the Zoe execution must be informed of the external URL it is exposed with. Zoe exposes an environment variable with this information, but it is up to the ZApp implementation to pass the correct options to the web application.

Configuration
^^^^^^^^^^^^^

* traefik-zk-ips : ZooKeeper addresses for storing dynamic configuration for træfik (ex.: ``z1:2181,z2:2181,z3:2181``)
* traefik-base-url : Base path used in reverse proxy URLs generated for træfik (default is ``/zoe/proxy/``)

ZApp description
^^^^^^^^^^^^^^^^

In the JSON description of ZApps, ports that need to be exposed through the reverse proxy need to have the ``proxy`` property set to ``true``. The property is optional and defaults to false, so by default no ports will be exposed via the reverse proxy.

Environment variables
^^^^^^^^^^^^^^^^^^^^^

ZApps can use the ``REVERSE_PROXY_PATH_<port number>`` environment variable to configure correctly the URL routing of web applications they contain. The value of these variables will be the concatenation of ``traefik-base-url`` and the unique key generated at runtime for each proxied port.

Access ZApps through Ingress Controller on Kubernetes
-----------------------------------------------------

Overview
^^^^^^^^
* We can access Zapps through a web proxy, so we do not need to open too many ports due to security reasons.
* This can be achieved when Zoe runs on Kubernetes by the support of an Ingress Controller.
* Automate the process of creating an ingress for a servive created by Zoe.
* Services which are exposed in Zapp can be accessed through the proxy url, which has the following format: ``http://servicename-executionid-deploymentname.proxy-path``

Requirements
^^^^^^^^^^^^
* A Kubernetes cluster which has:

  * Zoe
  * A (NGINX) ingress controller.
  * kubernetes-auto-ingress.

How it works
^^^^^^^^^^^^
1. Zoe configuration file:

 * ``--proxy-path``: the **ServerName** field in apache2 virtualhost configuration

2. (NGINX) ingress controller:

 * An Ingress is a collection of rules that allow inbound connections to reach the cluster services.
 * In order for the Ingress resource to work, the cluster must have an Ingress controller running. The Ingress controller will manage, configure the description in the Ingress resource to expose the associated services.

3. kubernetes-auto-ingress:

 * Currently, the process to submit an Ingress resource to the Ingress controller is manually done by cluster admins. kubernetes-auto-ingress automates this process. Every services have the labels "auto-ingress/enabled" is "enabled" will be automatically attached with the associated ingress resources.

References
^^^^^^^^^^
* Kubernetes Ingress: https://kubernetes.io/docs/concepts/services-networking/ingress/
* NGINX Ingress Controller: https://github.com/kubernetes/ingress/tree/master/controllers/nginx
* kubernetes-auto-ingress: https://github.com/hxquangnhat/kubernetes-auto-ingress
