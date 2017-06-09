.. _proxy:

Access ZApps through Ingress Controller on Kubernetes
=====================================================

Overview
--------
* We can access Zapps through a web proxy, so we do not need to open too many ports due to security reasons.
* This can be achieved when Zoe runs on Kubernetes by the support of an Ingress Controller.
* Automate the process of creating an ingress for a servive created by Zoe.
* Services which are exposed in Zapp can be accessed through the proxy url, which has the following format: ``http://servicename-executionid-deploymentname.proxy-path``

Requirements
------------
* A Kubernetes cluster which has:

  * Zoe
  * A (NGINX) ingress controller.
  * kubernetes-auto-ingress.

How it works
------------
1. Zoe configuration file:

 * ``--proxy-path``: the **ServerName** field in apache2 virtualhost configuration

2. (NGINX) ingress controller:

 * An Ingress is a collection of rules that allow inbound connections to reach the cluster services.
 * In order for the Ingress resource to work, the cluster must have an Ingress controller running. The Ingress controller will manage, configure the description in the Ingress resource to expose the associated services.

3. kubernetes-auto-ingress:

 * Currently, the process to submit an Ingress resource to the Ingress controller is mannually done by cluster admins. kubernetes-auto-ingress automates this process. Every services have the labels "auto-ingress/enabled" is "enabled" will be automatically attached with the associated ingress resources.

References
----------
* Kubernetes Ingress: https://kubernetes.io/docs/concepts/services-networking/ingress/
* NGINX Ingress Controller: https://github.com/kubernetes/ingress/tree/master/controllers/nginx
* kubernetes-auto-ingress: https://github.com/hxquangnhat/kubernetes-auto-ingress
