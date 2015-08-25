class ApplicationResources:
    def core_count(self):
        return 0


# For now resources are dictionaries and Platform recognizes:
# - memory_limit
# - worker_cores
class SparkApplicationResources(ApplicationResources):
    def __init__(self):
        self.master_resources = {}
        self.worker_resources = {}
        self.worker_count = 0

    def core_count(self) -> int:
        if "cores" in self.worker_resources:
            return self.worker_count * self.worker_resources["cores"]
        else:
            return 0
