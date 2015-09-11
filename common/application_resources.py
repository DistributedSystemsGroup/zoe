class ApplicationResources:
    def core_count(self):
        return 0

    def to_dict(self) -> dict:
        return {}


# For now resources are dictionaries and Platform recognizes:
# - memory_limit
# - worker_cores
class SparkApplicationResources(ApplicationResources):
    def __init__(self):
        self.master_resources = {}
        self.worker_resources = {}
        self.notebook_resources = {}
        self.client_resources = {}
        self.worker_count = 0
        self.container_count = 0

    def core_count(self) -> int:
        if "cores" in self.worker_resources:
            return self.worker_count * self.worker_resources["cores"]
        else:
            return 0

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret['master_resources'] = self.master_resources
        ret['worker_resources'] = self.worker_resources
        ret['notebook_resources'] = self.notebook_resources
        ret['client_resources'] = self.client_resources
        ret['worker_count'] = self.worker_count
        ret['container_count'] = self.container_count
        return ret
