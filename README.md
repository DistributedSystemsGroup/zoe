# Zoe - Container-based Analytics as a Service

This application uses Docker Swarm to run Analytics as a Service applications. Currently only Spark is supported, but we are planning inclusion of other frameworks.

It is composed of:

* zoe: command-line client
* zoe-scheduler: the main daemon that performs application scheduling and talks to Swarm
* zoe-web: the web service

## Requirements

* MySQL to keep all the state
* Docker Swarm
* A Docker registry containing Spark images
* Apache Web Server to act as a reverse proxy

## How to install

1. Clone this repository
2. Generate a sample configuration file with `zoe.py write-config zoe.conf`
3. Edit `zoe.conf` and check/modify the following sections (the other sections are covered below):
    * flask (use in a python interpreter `import os; os.urandom(24)` to generate a new key)
    * filesystem
    * smtp
4. Setup supervisor to manage Zoe processes: in the `scripts/supervisor/` directory you can find the configuration file for
   supervisor. You need to modify the paths to point to where you cloned Zoe.
5. Start running applications!

Zoe configuration is read from an 'ini' file, the following locations are searched for a file names `zoe.conf`:
* working path (.)
* /etc/zoe

### DB

1. Install MySQL/MariaDB, or any other DB supported by SQLAlchemy.
2. Create a database, a user and a password and use these to build a connection string like `mysql://<user>:<password>@host/db`
3. Put this string in section `[db]` of zoe.conf

### Swarm/Docker

Install Docker and the Swarm container:
* https://docs.docker.com/installation/ubuntulinux/
* https://docs.docker.com/swarm/install-manual/

For testing you can use a Swarm with a single Docker instance located on the same host/VM.

#### Network configuration

Zoe assumes that containers placed on different hosts are able to talk to each other freely. Since we use Docker on bare metal, we
use an undocumented network configuration, with the docker bridges connected to a physical interface, so that
containers on different hosts can talk to each other on the same layer 2 domain.
To do that you need also to reset the MAC address of the bridge, otherwise bridges on different hosts will have the same MAC address.

Other configurations are possible, but configuring Docker networking is outside the scope of this document.

#### Images: Docker Hub Vs local Docker registry

The images used by Zoe are available on the Docker Hub:

* https://hub.docker.com/r/zoerepo/spark-scala-notebook/
* https://hub.docker.com/r/zoerepo/spark-master/
* https://hub.docker.com/r/zoerepo/spark-worker/
* https://hub.docker.com/r/zoerepo/spark-submit/

Since the Docker Hub can be quite slow, we strongly suggest setting up a private registry. The `build_images.sh` script in the
[zoe-docker-images](https://github.com/DistributedSystemsGroup/zoe-docker-images) repository can help you populate the registry
bypassing the Hub.

The images are quite standard and can be used also without Zoe. Examples on how to do that, are available in the `scripts/start_cluster.sh` script.

Set the registry address:port in section `[docker]` in `zoe.conf`. If use Docker Hub, set the option to an empty string.

### Apache Web Server configuration
Install the Apache web server.

A sample virtual host file containing the directives required by Zoe is available in `scripts/apache-sample.conf`.

This configuration will also proxy zoe-web, that starts on port 5000 by default.

Please note that putting the generated config file in /tmp can be a serious security problem, depending on your setup.

Zoe generates dynamically proxy entries to let users access to the various web interfaces contained in the Spark containers.
To do this, it needs to be able to reload Apache and to write to a configuration file included in the VirtualHost directive.

Zoe is executing `sudo service apache2 reload` whenever nedded, so make sure the user that runs Zoe is able to run that command
succesfully.

Change as needed the options `web_server_name`, `access_log` and `proxy_config_file` in the section `[apache]` of `zoe.conf`.