class SparkClusterDescription:
    def __init__(self):
        self.num_workers = 2
        self.executor_ram_size = "4g"
        self.worker_cores = "2"

    def for_spark_notebook(self):
        self.num_workers = 2
        self.worker_cores = "2"
        self.executor_ram_size = "4g"
