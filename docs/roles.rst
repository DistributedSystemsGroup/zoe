.. _roles:

Roles
=====

Roles in Zoe define the limits of what a user can do. A role can be assigned to multiple users, but a user can have only a single role.

The capabilities that can be turned on and off for a role are:

 * can_see_status : can access the status page on the web interface
 * can_change_config : can make changes to the configuration (add/delete/modify users, quotas and roles)
 * can_operate_others : can operate on others' work (see and terminate other users' executions)
 * can_delete_executions : can permanently delete executions and all the associated logs
 * can_access_api : can access the REST API
 * can_customize_resources : can use the web interface to modify resource reservations when starting ZApps from the shop
 * can_access_full_zapp_shop : has access to all ZApps in the shop

By default three roles are created:

 * admin : all capabilities are set
 * superuser : has can_see_status, can_access_api, can_customize_resources and can_access_full_zapp_shop
 * user : has no capabilities

Zoe will refuse to delete or modify the admin role.
