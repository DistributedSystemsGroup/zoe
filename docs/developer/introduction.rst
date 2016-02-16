General design decisions
========================

Zoe uses an internal state class hierarchy, with a checkpoint system for persistence and debug. This has been done because:
* Zoe state is small
* Relations between classes are simple
* SQL adds a big requirement, with problems for redundancy and high availability
* Checkpoints can be reverted to and examined for debug

For now checkpoints are created each time the state changes.

Authentication: HTTP basic auth is used, as it is the simplest reliable mechanism we could think of. It can be easily secured by adding SSL. Server-side ``passlib`` guarantees a reasonably safe storage of salted password hashes.
There advantages and disadvantages to this choice, but for now we wnat to concentrate on different, more core-related features of Zoe.

Synchronous API. The Zoe Scheduler is not multi-thread, all requests to the API are served immediately. Again, this is done to keep the system simple and is by no means a decision set in stone.
