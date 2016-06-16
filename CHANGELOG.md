# Zoe Changelog

## Version 0.10.0

* This version is the start of a new series of releases moving toward a new architecture
* Only one overlay network (created by the sysadmin) will be used by all Zoe executions. We provide Dockerfiles for SOCKS and SSHd containers that can be used to give users access inside the Zoe overlay network. These containers will no longer be managed by Zoe.
* Move the REST API in the web process and add a ZeroMQ-based API between the web and the master.
* Move all user management in the web process.
* Use Postgresql to store the state

## Version 0.9.7

* Check application description version during validation.
* Bump application description version to 2 since we are going to make some major changes in the format
* Add fields `total_count`, `essential_count` and `startup_order` to service descriptions.
* Comment code related to the parsing of cluster statistics from Swarm. The data returned by API changes too often and parsing it consistently is too complex. A bug is open on the Swarm issue tracker.

## Version 0.9.6

* Workspaces: Zoe now supports starting containers with a directory from the hosts mounted as a volume. The directory is private for the user and is not wiped when the Zoe execution terminates. There are some issues with file permissions when the container images define users with arbitrary UIDs.
* Add an error status and error message visible to the user when Zoe fails starting an execution
* Add a Docker Compose file to help test deployments
* The gateway container image is now configurable
* Move applications to their own repository (zoe-applications)
* Move the Zoe logger code into its own repository
* Update the stats module to the latest Docker version. Since the Python Docker API refuses to provide machine readable output, we have to stay locked to Docker versions
* Add date and time to log output produced by Zoe processes
* Expand the web interface, users can now list, start, terminate and restart executions
