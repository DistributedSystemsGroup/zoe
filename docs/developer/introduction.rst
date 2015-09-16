General design decisions
========================

SQLAlchemy sessions
-------------------

To manage sessions, SQLAlchemy provides a lot of flexibility, with the ``sessionmaker()`` and the ``scoped_session()`` functions.

In Zoe we decided to have a number of "entry points", where a session can be created and closed. These entry points correspond to the thread loops:
* The scheduler main loop
* The tasks
* The IPC server (for now it not multi-threaded, but each request generates a new session and closes it at the end)

Sessions should never be created anywhere else, outside of these functions.
