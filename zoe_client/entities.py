import dateutil.parser


def deserialize_datetime(isoformat):
    if isoformat is None:
        return None
    else:
        return dateutil.parser.parse(isoformat)


class User:
    def __init__(self, user: dict):
        self.id = user['id']
        self.email = user['email']


class Execution:
    def __init__(self, execution: dict):
        self.id = execution['id']
        self.name = execution['name']
        self.assigned_resources = execution['assigned_resources']
        self.application_id = execution['application_id']
        self.time_started = deserialize_datetime(execution['time_started'])
        self.time_scheduled = deserialize_datetime(execution['time_scheduled'])
        self.time_finished = deserialize_datetime(execution['time_finished'])
        self.status = execution['status']
        self.termination_notice = execution['termination_notice']
        self.cluster_id = execution['cluster_id']
        self.type = execution['type']

        if self.type == 'spark-submit-application':
            self.commandline = execution['commandline']
            self.spark_opts = execution['spark_opts']

        self.containers = []

        for c in execution['containers']:
            self.containers.append(Container(c))


class Container:
    def __init__(self, container: dict):
        self.id = container['id']
        self.docker_id = container['docker_id']
        self.cluster_id = container['cluster_id']
        self.ip_address = container['ip_address']
        self.readable_name = container['readable_name']

        self.proxies = []

        for p in container['proxies']:
            self.proxies.append(Proxy(p))


class Proxy:
    def __init__(self, proxy: dict):
        self.id = proxy['id']
        self.internal_url = proxy['internal_url']
        self.cluster_id = proxy['cluster_id']
        self.container_id = proxy['container_id']
        self.service_name = proxy['service_name']
        self.last_access = deserialize_datetime(proxy['last_access'])


class Application:
    """
    :type id: int
    :type name: str
    :type required_resources: ApplicationResources
    :type user_id: int
    :type type: str
    :type master_image: str
    :type worker_image: str
    :type notebook_image: str
    :type submit_image: str
    :type executions: list[Execution]
    """
    def __init__(self, application: dict):
        self.id = application['id']
        self.name = application['name']
        self.required_resources = application['required_resources']
        self.user_id = application['user_id']
        self.type = application['type']
        if 'spark' in self.type:
            self.master_image = application['master_image']
            self.worker_image = application['worker_image']
        if self.type == 'spark-notebook':
            self.notebook_image = application['notebook_image']
        if self.type == 'spark-submit':
            self.submit_image = application['submit_image']

        self.executions = []

        for e in application['executions']:
            self.executions.append(Execution(e))
