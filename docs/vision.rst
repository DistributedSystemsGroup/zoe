.. _vision:

The vision for Zoe Analytics
============================

Zoe focus is data analytics. This focus helps defining a clear set of objectives and priorities for the project and avoid the risk of competing directly with generic infrastructure managers like Kubernetes or Swarm. Zoe instead sits on top of these "cloud managers" to provide a simpler interface to end users who have no interest in the intricacies of container infrastructures.

Data analytic applications do not work in isolation. They need data, that may be stored or streamed, and they generate logs, that may have to be analyzed for debugging or stored for auditing. Data layers, in turn, need health monitoring. All these tools, frameworks, distributed filesystems, object stores, form a galaxy that revolves around analytic applications. For simplicity we will call these "support applications".

Zoe does not focus on support applications. Managing a stable and fault tolerant HDFS cluster, for example, is a task for tools like Puppet, Chef or Ansible and is done by system administrators. Zoe, instead, targets data scientists, that need to use a cluster infrastructure, but do not usually have sysadmin skills.

Kinds of applications
---------------------

See :ref:`zapp_classification`.
