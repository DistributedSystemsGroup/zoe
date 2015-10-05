.. _vision:

The motivation behind Zoe
=========================

The fundamental idea of Zoe is that a user who wants run data analytics applications should not be bothered by systems details, such as how to configure the amount
of RAM a Spark Executor should use, how many cores are available in the system or even how many worker nodes should be used to meet an execution deadline.

Moreover we feel that there is a lack of solutions in the field of private clouds, where resources are not infinite and data layers (data-sets) may be shared between
different users. All the current Open Source solutions we are aware of target the public cloud use case and try to, more or less, mimic what Amazon and other big
names are doing in their data-centers.

Zoe strives to satisfy the following requirements:

* easy to use for the end-user
* easy to manage for the system administrator, easy to integrate in existing data-centers/clouds/VM deployments
* short (a few seconds) reaction times to user requests or other system events
* smart queuing and scheduling of applications when resources are critical

OpenStack Sahara, Mesos and YARN are the projects that, each in its own way, try to solve at least part of our needs.

OpenStack Sahara
----------------
We know well `OpenStack Sahara <https://wiki.openstack.org/wiki/Sahara>`_, as we wrote the Spark plugin and contributed it to that project. We
feel that Sahara has limitations in:

* software support: Sahara plugins support a limited set of data-intensive frameworks, adding a new one means writing a new Sahara plugin and even adding support
  for a new version requires going through a one-two week (on average) review process.
* lack of scheduling: Sahara makes the assumption that you have infinite resources. When you try to launch a new cluster and there are not enough resources available,
  the request fails and the user is left doing application and resources scheduling by hand.
* usability: setting up everything that is needed to run an EDP job is cumbersome and error-prone. The user has to provide too many details in too many different places.

Moreover changes to Sahara needs to go through a lengthy review process, that on one side tries to ensure high quality, but on the other side slows down development,
especially of major architectural changes, like the ones needed to address the concerns listed above.

Mesos
-----

Mesos is marketing itself as a data-center operating system. Zoe has no such high profile objective: while Zoe schedules distributed applications, it has
not knowledge of the applications it is scheduling and, even more importantly, does not require any change in the applications themselves to be run in Zoe.

Mesos requires that each application provides two Mesos-specific components: a scheduler and an executor. Zoe has not such requirements.

YARN
----

YARN, from our point of view, has many similarities with Mesos. It requires application support. Moreover it is integrated in the Hadoop distribution and,
while recent efforts are pushing toward making YARN stand up on its own, it is currently tailored for Hadoop applications. Finally YARN does not use Docker
containers.
