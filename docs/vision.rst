.. _vision:

Vision for Zoe
==============

Zoe focus is data analytics. This focus helps defining a clear set of objectives and priorities for the project and avoid the risk of competing directly with generic infrastructure managers like Kubernetes or Swarm. Zoe instead sits on top of these "cloud operating systems" to provide a simpler interface to end users who have no interest in the intricacies of container infrastructures.

Data analytic applications do not work in isolation. They need data, that may be stored or streamed, and they generate logs, that may have to be analyzed for debugging or stored for auditing. Data layers, in turn, need health monitoring. All these tools, frameworks, distributed filesystems, object stores, form a galaxy that revolves around the analytic applications. For simplicity we will call these "support applications".

To offer an integrated, modern solution to data analysis Zoe must support both analytic and support applications, even if they have very different users and requirements.

The users of Zoe
----------------

- users: the real end-users, who submit non-interactive analytic jobs or use interactive applications
- admins: systems administrators who maintain Zoe, the data layers, monitoring and logging for the infrastructure and the apps being run

Deviation from the current ZApp terminology
-------------------------------------------

In the current Zoe implementation (0.10.x) ZApps are self-contained descriptions of a set of cooperating processes. They get submitted once, to request the start-up of an execution. This fits well the model of a single spark job or of a throw-away jupyter notebook.

We need to revise a bit this terminology: ZApps remain the top level, user-visible entity. The ZApp building blocks, analytic engines or support tools, are called frameworks. A framework, by itself, cannot be run. It lacks configuration or a binary to execute, for example. Each framework is composed of one or more processes.

A few examples:

- A jupyter notebook, by itself, is a framework in Zoe terminology. It lacks configuration that tells it which kernels to enable or on which port to listen to. It is a framework composed by just one process.
- A Spark cluster is another framework. By itself it does nothing. It can be connected to a notebook, or it can be given a jar file and some data to process.

To create a ZApp you need to put together one or more frameworks and add some configuration (framework-dependent) that tells the framework(s) how to behave.

A ZApp shop could contain both frameworks (that user must combine together) and full-featured ZApps, whenever it is possible.

Nothing prevents certain ZApp attributes to be "templated", like resource requests or elastic process counts, for example.

Kinds of applications
---------------------

See :ref:`zapp_classification`.

The concept of application in Zoe is very difficult to define, as it is very fluid and encloses a lot of different tools, frameworks, interfaces, etc.

The focus on analytic applications helps in giving some concrete examples and use cases.

There two main categories of use-cases:

- long-running executions
- data processing workflows

Long-running executions
^^^^^^^^^^^^^^^^^^^^^^^

In this category we have:

- interactive applications started by users (a Jupyter Notebook for example)
- support applications started by admins

  - data layers
  - monitoring tools

These applications are static in nature. Once deployed they need to be maintained for an indefinite amount of time. A data layer can be expanded with new nodes, or a monitoring pipeline can be scaled up or down, but these are events initiated manually by admins or performed automatically following administrative policies.

Interactive applications (usually web interfaces) can be stand-alone data analysis tools or can be connected to distributed data intensive frameworks. As a matter of fact, a user may start working on a stand-alone interface and then connect the same interface to bigger and bigger clusters to test his algorithm with more and more data.

Workflows
^^^^^^^^^
A few examples of workflows:

- run a single job (simplest kind of workflow)
- run a job every hour (triggered by time)
- run a set of jobs in series or in parallel (triggered by the state of other jobs)
- run a job whenever the size of a file/directory/bucket on a certain data layer reaches 5GB (more complex trigger)
- combinations of all the above

A complete workflow system for data analytic is very complex and is a whole different project that runs on top of Zoe core functionality. Zoe-workflow should be implemented incrementally, starting with the basics. When it reaches a certain complexity, then it should be spun-out in its own project.

At the beginning, workflows can be made up of self-ending applications only. Integrating streaming applications should be done later on.

Commands to the system
----------------------

Zoe manages requests to change the state of a set of resources (a virtual or physical cluster of machines) by starting, terminating or modifying process containers.

Users should be kept as much as possible ignorant of the inner workings of these state changes and should be able to express high level commands, like:

- start this application (-> creates one or more executions)
- terminate this execution(s)
- Attach to this Jupyter notebook this new Spark cluster
- Define a workflow (see the workflow section)

These kind of commands should be translated automatically into Zoe state changes that are then applies by the components at the lower levels of the Zoe architecture.

In addition to the commands above, admins should also be able to define operations on long-running executions:

- request rolling or standard upgrades (find all containers using a certain image v. 1 and upgrade them to version 2)
- start and scale long-running applications
- define non-ephemeral storage volumes for data layer applications
- terminate (should be well protected, may cause data losses)

