.. _zapp_classification:

Classification
==============

Zoe runs processes inside containers and the Zoe application description is very generic, allowing any kind of application to be described in Zoe and submitted for execution. While the main focus of Zoe are so-called "analytic applications", there are many other tools that can be run on the same cluster, for monitoring, storage, log management, history servers, etc. These applications can be described in Zoe and executed, but they have quite different scheduling constraint.

Please note that in this context an "elastic" service is a service that "can be automatically resized". HDFS can be resized, but it is done as an administrative operation that requires setting up partitions and managing the network and disk load caused by rebalancing. For this reason we do not consider it as "elastic".

- Long running: potentially will never terminate

  - Non elastic

    - Storage: need to have access to non-container storage (volumes or disk partitions)

      - HDFS
      - Cassandra
      - ElasticSearch

    - Interactive: need to expose web interfaces to the end user

      - Jupyter
      - Spark, Hadoop, Tensorflow, etc history servers
      - Kibana
      - Graylog (web interface only)

    - Streaming:

      - Logstash

    - User access

      - Proxies and SSH gateways

  - Elastic (can be automatically resized)

    - Streaming:

      - Spark streaming user jobs
      - Storm
      - Flink streaming
      - Kafka

- Ephemeral: will eventually finish by themselves

  - Elastic:

    - Spark classic batch jobs
    - Hadoop MapReduce
    - Flink

  - Non elastic:

    - MPI
    - Tensorflow

All the applications in the **long-running** category need to be deployed, managed, upgraded and monitored since they are part of the cluster infrastructure. The Jupyter notebook at first glance may seem out of place, but in fact it is an interface to access different computing systems and languages, sometimes integrated in Jupyter itself, but also distributed in other nodes, with Spark or Tensorflow backends. As an interface the user may expect for it to be always there, making it part of the infrastructure.

The **elastic, long-running** applications have a degree more of flexibility, that can be taken into account by Zoe. They all have the same needs as the non-elastic applications, but they can also be scaled according to many criteria (priority, latency, data volume).

The applications in the **ephemeral** category, instead, will eventually terminate by themselves: a batch job is a good example of such applications.
