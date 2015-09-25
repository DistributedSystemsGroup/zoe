class Container:
    def __init__(self, container: dict):
        self.id = container['id']
        self.docker_id = container['docker_id']
        self.cluster_id = container['cluster_id']
        self.ip_address = container['ip_address']
        self.readable_name = container['readable_name']