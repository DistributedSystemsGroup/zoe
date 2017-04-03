.. _proxy:

Access ZApps through proxy
==========================

Overview
--------
* We can access Zapps through a web proxy, so we do not need to open too many ports due to security reasons.
* The Zapps will be preconfigured the ``base_url`` or ``context_path`` when building image.
* By using a web proxy, services which are exposed in Zapp can be access through the proxy url, which has the following format: ``base_proxy_path/zoe/userID/executionID/serviceName``

Requirements
------------
* A web proxy. We use **Apache2** as the default one.
* The service which is needed to be accessed through web proxy needs to support running in ``base_url`` or ``context_path`` and is defined as expose: True in the zap description.
* Specify the environment key, value in zapp description to specify the base_url, the value will be overridden by Zoe to assure the format of the proxy url.

How it works
------------
1. Zoe configuration file:

 * ``--proxy-type``: web proxy type to be used, default is Apache, Nginx can be added in future
 * ``--proxy-container``: the container which we run the proxy web server
 * ``--proxy-config-file``: the configuration (VirtualHost configuration file) file path of the proxy web server
 * ``--proxy-path``: the **ServerName** field in apache2 virtualhost configuration

2. Proxy server:

 * Apache web server is running inside a container, default is named as ``apache2``
 * Apache configuration file inside ``/apache2_installation_path/sites-available``, default is ``zoe.conf``
 * ``mod_proxy``, ``modproxyhttp`` much be enabled

3. Zoe:

 * Services supports to configure ``base_url`` via environment variables, Zoe will get those environment variables and generate the proxy path for each service which is defined as ``expose: True``, then passes them as containers’ options to create containers.
 * When **starting a new execution**, after all services have **started** states, Zoe begins to **proxify** them. It will:

   * Connect to the ``apache2`` container and adds new entries to the ``zoe.conf`` these lines:

     * ``ProxyPass /base_proxy_path/zoe/userID/executionID/serviceName http://ip:port``
     * ``ProxyPassReverse /base_proxy_path/zoe/userID/executionID/serviceName http://ip:port``
     * Which:

       * IP: IP of the host which the container is running on
       * Port: the binding port at the host
   * Reload the ``apache2`` service running inside the ``apache2`` container
 * When terminating an execution, the **unproxify** process happens, which is similar to the proxifying process. Instead of inserting new entries, it deletes entries which corresponding to the terminating execution.

Note
----
* The proxifying and unproxifying process can be done manually: you can go directly to the proxy server container and add entries into the configuration file then reload the service
* The current proxy server we use is Apache2. Nginx proxy server can be added in future with the same idea.

References
----------
* Apache web server: https://httpd.apache.org/
* Apache reverse proxy: https://httpd.apache.org/docs/2.4/mod/mod_proxy.html
* Apache virtualhost example: https://httpd.apache.org/docs/2.4/vhosts/examples.html
