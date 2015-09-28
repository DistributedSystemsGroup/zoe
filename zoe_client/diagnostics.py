from zoe_client.lib.ipc import ZoeIPCClient
from zoe_client.scheduler_classes.execution import Execution
from zoe_client.scheduler_classes.container import Container


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


def execution_exposed_url(execution: Execution):
    for c in execution.containers:
        assert isinstance(c, Container)
        port = c.description.exposed_endpoint()
        if port is not None:
            return port.get_url(c.ip_address)
