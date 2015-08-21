class ApplicationResources:
    pass

# For now resources are dictionaries and Platform recognizes:
# - memory_limit
# - worker_cores
class SparkApplicationResources(ApplicationResources):
    def __init__(self):
        self.master_resources = {}
        self.worker_resources = {}
        self.worker_count = 0
