# Zoe Changelog

## Version 0.9.7

* Check application description version during validation.
* Bump application description version to 2 since we are going to make some major changes in the format
* Add fields `total_count`, `essential_count` and `startup_order` to service descriptions.

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
