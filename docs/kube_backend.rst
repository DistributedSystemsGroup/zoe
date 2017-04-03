.. _kube-backend:

Kubernetes backend for Zoe
==========================

Overview
--------
* Running Zoe on a Kubernetes cluster instead of Swarm
* Support High availability for Zapp services

Requirements
------------
* A running Kubernetes cluster, version 1.4.7
* pykube python library, version >=0.14.0

How it works
------------
1. Zoe configuration file:

 * ``--backend``: put Kubernetes instead of Docker Swarm
 * ``--kube-config-file``: the configuration file of Kubernetes cluster

2. Zoe:

* Zapp Description:

  * Add new field: ``replicas``, if users doesn't specify this value, the default value for each service would be ``1``.
  * In field ``require_resources``, the ``cores`` field can be float.

* Idea:

  * Create each **replication controller** per each service of a Zapp. Replication Controller assures to have at least a number of **replicas** (pod) always running.
  * Create a Kubernetes **service** per each **replication controller**, which has the same **labels** and **label selectors** with the associated **replication controller**. The service would help the zapp service be exposed to the network by exposing the same port of the service on all kubernetes nodes.

References
----------
* Kubernetes: https://kubernetes.io/
* Kubernetes Replication Controller : https://kubernetes.io/docs/user-guide/replication-controller/
* Kubernetes Service: https://kubernetes.io/docs/user-guide/services/
* Kubernetes Limit and Request: https://kubernetes.io/docs/user-guide/compute-resources/

