from zoe_client.lib.ipc import ZoeIPCClient


# Logs
def log_get(container_id: int) -> str:
    ipc_client = ZoeIPCClient()
    answer = ipc_client.ask('log_get', container_id=container_id)
    if answer is not None:
        return answer['log']


# Platform
def platform_stats() -> dict:
    ipc_client = ZoeIPCClient()
    stats = ipc_client.ask('platform_stats')
    return stats


# Containers
def container_stats(container_id):
    ipc_client = ZoeIPCClient()
    return ipc_client.ask('container_stats', container_id=container_id)
