.. _users:

Users
=====

Zoe has a flexible user management system. All users that need access to Zoe need to have an entry created in the Zoe user database through the command-line utility (zoe-admin.py) or the web interface.

When the entry is being created, the administrator can choose an authentication source, that can be different for each user. Currently the following sources are available:

 * internal : the password is stored in Zoe
 * LDAP(+SASL) : authentication is performed by contacting an external LDAP server
 * textfile : the password is stored in a CSV file
 * pam : authentication is performed by using the PAM subsystem of the operating system where the zoe-api process is running

More backends can be developed, the authentication system is designed to be pluggable.

Each user has a :ref:`roles` and a :ref:`quotas` associated.

By default Zoe has an admin user (password admin), created during the first startup. While deploying Zoe, this user must be disabled or its password changed. The default password is a security risk.

