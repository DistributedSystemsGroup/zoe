# Zoe - Container Analytics as a Service

This application uses a Docker Swarm cluster to run on-demand Spark clusters.

IT is composed of three components:

* zoectl: command-line client
* zoe-scheduler: the main daemon that performs application scheduling and talks to Swarm
* zoe-web: the web service

## Requirements

* MySQL to keep all the state
* Docker Swarm
* A Docker registry containing Spark images
* Apache to act as a reverse proxy

## Apache configuration

Put this in your virtual host entry:
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
IncludeOptional /tmp/zoe-proxy.conf*
```

If you need to proxy the web application itself, add also these directives:
```
<Location /web/>
    ProxyHtmlEnable On
    ProxyHTMLExtended On
    ProxyPass http://192.168.45.25:5000/web/
    ProxyPassReverse http://192.168.45.25:5000/web/
    ProxyHTMLURLMap /web/ /web/
</Location>
<Location /api/>
    ProxyHtmlEnable On
    ProxyHTMLExtended On
    ProxyPass http://192.168.45.25:5000/api/
    ProxyPassReverse http://192.168.45.25:5000/api/
    ProxyHTMLURLMap /api/ /api/
</Location>
```

The script `apache-proxy.py` needs to be run to update apache whenever containers are created or destroyed.