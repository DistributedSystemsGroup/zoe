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


class Application:
    """
    :type id: int
    :type user_id: int
    :type description: dict
    :type executions: list[Execution]
    """
    def __init__(self, application: dict):
        self.id = application['id']
        self.description = application['description'].copy()
        self.user_id = application['user_id']

        self.executions = []

        for e in application['executions']:
            self.executions.append(Execution(e))
