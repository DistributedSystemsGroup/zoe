.. _quotas:

Quotas
======

Quotas enforce resource limits to users. A quota can be assigned to multiple users, but a user can have one quota.

Quotas can be set on the following resources:

 * concurrent_executions : maximum number of concurrent executions in an active state
 * memory : maximum amount of memory a user can reserve in total, across all its active executions
 * cores : maximum amount of cores a user can reserve in total, across all its active executions
 * runtime_limit : maximum time an execution is permitted to run

A default quota is always available:

 * name: default
 * concurrent executions: 5
 * memory: 32GB
 * cores: 20
 * runtime_limit: 24 hours

This default quota can be modified, but not deleted. More quotas can be created via the zoe_admin.py command or the web interface.
