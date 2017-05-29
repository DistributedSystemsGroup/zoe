.. _logging:

Container logs
==============

By design Zoe does not involve itself with the output from container processes. The logs can be retrieved with the usual Docker command ``docker logs`` while a container is alive, they are lost forever when the container is deleted. This solution however does not scale very well: to examine logs, users need to have access to the docker commandline tools and to the Swarm they are running in.

In production we recommend to configure your backend to manage the logs according to your policies. Docker Engines, for example, can be configured to send standard output and error to a remote destination in GELF format (others are supported), as soon as they are generated.

A popular logging stack that supports GELF is `ELK <https://www.elastic.co/products>`_. However, in our experience, web interfaces like Kibana or Graylog are not useful to the Zoe users: they want to quickly dig through logs of their executions to find an error or an interesting number to correlate to some other number in some other log. The web interfaces are slow and cluttered compared to using grep on a text file.
Which alternative is good for you depends on the usage pattern of your users, your log auditing requirements, etc.
