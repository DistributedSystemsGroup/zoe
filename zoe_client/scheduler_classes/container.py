from common.application_description import ZoeApplicationProcess


class Container:
    """
    :type id: int
    :type docker_id: str
    :type cluster_id: int
    :type ip_address: str
    :type readable_name: str
    :type description: ZoeApplicationProcess
    """
    def __init__(self, container: dict):
        self.id = container['id']
        self.docker_id = container['docker_id']
        self.cluster_id = container['cluster_id']
        self.ip_address = container['ip_address']
        self.readable_name = container['readable_name']
        self.description = ZoeApplicationProcess.from_dict(container['description'])
