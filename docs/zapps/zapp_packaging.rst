.. _zapp_packaging:

A new ZApp format
=================

* Remove the substitution language

All information from Zoe is passed in predefined environment variables:

* ZOE_EXECUTION_NAME
* ZOE_EXECUTION_ID
* ZOE_SERVICE_GROUP : name of the service as given in the ZApp description
* ZOE_SERVICE_NAME : name of the service instance
* ZOE_SERVICE_ID
* ZOE_OWNER
* ZOE_DEPLOYMENT_NAME
* ZOE_MY_DNS_NAME
* ZOE_EXECUTION_SERVICE_LIST : comma-separated list of all the DNS names of the other services in this execution

A number of volumes will be mounted on all containers:

* User workspace, same for all containers of a certain user, mounted at /workspace
* Logs, different for each container, mounted at /logs

A Zoe script will be the entrypoint for all ZApp containers. If a command is specified for a container, it must be a user-specified script that will be run by the Zoe script.


Packaging
---------

ZApps will be distributed as self-contained set of files with this structure:

* app.json : ZApp description (the current one with a few changes)
* icon.png : an icon to be shown on graphical interfaces
* metadata.json : metadata for the app and options that can be set to modify the app behaviour
* docker/
  * docker/image1/Dockerfile : the dockerfile needed to build the image for service 1
  * docker/image1/* : all the other files required to build the image for service 1
  * ...
  * docker/imageN/Dockerfile : the dockerfile needed to build the image for service N
  * docker/imageN/* : all the other files required to build the image for service N

ZApps can be moved as tar/zip archives, downloaded via a website or cloned from github.
