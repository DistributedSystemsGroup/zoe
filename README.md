# Zoe - Container Analytics as a Service

This application uses Docker Swarm to run on-demand Spark clusters.

It is composed of three components:

* zoectl: command-line client
* zoe-scheduler: the main daemon that performs application scheduling and talks to Swarm
* zoe-web: the web service

## Requirements

* MySQL to keep all the state
* Docker Swarm
* A Docker registry containing Spark images
* Redis
* Apache to act as a reverse proxy

## Configuration

Zoe configuration is kept, for now, in a Python file: `common/configuration.py`

The cookie secret key is defined in `zoe_web/__init__.py`.

### Swarm/Docker

For testing you can use also a single Docker instance, just set its endpoint in the configuration file mentioned above.

To use Swarm, we use an undocumented network configuration, with the docker bridges connected to a physical interface, so that
containers on different hosts can talk to each other on the same layer 2 domain.

### Images: Docker Hub Vs local Docker registry

The images used by Zoe are available on the Docker Hub:

* https://hub.docker.com/r/zoerepo/spark-scala-notebook/
* https://hub.docker.com/r/zoerepo/spark-master/
* https://hub.docker.com/r/zoerepo/spark-worker/
* https://hub.docker.com/r/zoerepo/spark-submit/

Since the Docker Hub can be quite slow, we strongly suggest setting up a private registry. The `build_images.sh` script in the
[zoe-docker-images](https://github.com/DistributedSystemsGroup/zoe-docker-images) repository can help you populate the registry
bypassing the Hub.

The images are quite standard and can be used also without Zoe, for examples
on how to do that, see the `scripts/start_cluster.sh` script.

### Redis

Redis is used for storing Spark applications and logs, in zip archives. It is not the best use of redis, but it provides a
very simple to use interface. We are looking for a different solution and this requirement will likely disappear soon.

### Apache configuration

Zoe generates dynamically proxy entries to let users access to the various web interfaces contained in the Spark containers.
To do this, it needs to be able to reload Apache and to write to a configuration file included in the VirtualHost directive.

Here is an example configuration for a virtual host:
```
ProxyHTMLLinks a href
ProxyHTMLLinks area href
ProxyHTMLLinks link href
ProxyHTMLLinks img src longdesc usemap
ProxyHTMLLinks object classid codebase data usemap
ProxyHTMLLinks q cite
ProxyHTMLLinks blockquote cite
ProxyHTMLLinks ins cite
ProxyHTMLLinks del cite
ProxyHTMLLinks form action
ProxyHTMLLinks input src usemap
ProxyHTMLLinks head profile
ProxyHTMLLinks base href
ProxyHTMLLinks script src for

ProxyHTMLEvents onclick ondblclick onmousedown onmouseup \
    onmouseover onmousemove onmouseout onkeypress \
    onkeydown onkeyup onfocus onblur onload \
    onunload onsubmit onreset onselect onchange

ProxyRequests Off

<Location />
        ProxyHtmlEnable On
        ProxyHTMLExtended On
        ProxyPass http://127.0.0.1:5000/ retry=0
        ProxyPassReverse http://127.0.0.1:5000/
</Location>

IncludeOptional /tmp/zoe-proxy.conf*
```

This configuration will also proxy zoe-web, that starts on port 5000 by default.

Please note that putting the generated config file in /tmp can be a serious security problem, depending on your setup.
