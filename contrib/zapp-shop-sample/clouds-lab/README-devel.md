# Jupyter Notebook image

This image contains the Jupyter notebook configured with Pythen and a Spark client. It is used by Zoe, the Container Analytics as a
Service system to create on-demand notebooks connected to containerized Spark clusters.

Zoe can be found at: https://github.com/DistributedSystemsGroup/zoe

## Setup

The Dockerfile runs a start script that configures the Notebook using these environment variables:

* SPARK\_MASTER\_IP: IP address of the Spark master this notebook should use for its kernel
* PROXY\_ID: string to use as a prefix for URL paths, for reverse proxying
* SPARK\_EXECUTOR\_RAM: How much RAM to use for each executor spawned by the notebook

# Spark Scala master image

This image contains the Scala master process. It is used by Zoe, the Container Analytics as a
Service system to create on-demand Spark clusers in Spark standalone mode.

Zoe can be found at: https://github.com/DistributedSystemsGroup/zoe

## Setup

The Dockerfile automatically starts the Spark master process when the container is run.

# Spark worker image

This image contains the Scala worker process. It is used by Zoe, the Container Analytics as a
Service system to create on-demand Spark clusters in standalone mode.

Zoe can be found at: https://github.com/DistributedSystemsGroup/zoe

## Setup

The Dockerfile runs the worker process when run. The following options can be passed via environment variables:

* SPARK\_MASTER\_IP: IP address of the Spark master this notebook should use for its kernel
* SPARK\_WORKER\_RAM: How much RAM the worker can use (default is 4g)
* SPARK\_WORKER\_CORES: How many cores can be used by the worker process (default is 4)

