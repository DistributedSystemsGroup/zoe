General design decisions
========================

In this architecture we overturned our previous decision of keeping state internal, with periodic checkpointing.
State is kept in Postgres and shared among the different Zoe components. For a distributed system an external database simplifies enormously many common situation, with transactions and strong guarantees of consistency.

User management is left out of Zoe as much as possible. User authentication backends provide just a minimum of information for Zoe: a user ID and a role. Zoe does not manage creation, deletion, passwords, etc.

Zoe is distributed and uses threads to keep the APIs responsive at all times.

Object naming
-------------
Database IDs are used to identify executions and services. Container names within Docker Swarm must be unique, we decided to produce names that give some information to the administrator who looks at the output of ``docker ps`` instead of using opaque UUIDs. In addition, these same names are exposed by standard monitoring tools.
