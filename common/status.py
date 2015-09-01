from pprint import pformat

from zoe_scheduler.swarm_status import SwarmStatus
from common.state import Application, Execution, SparkSubmitExecution


class Report:
    def __init__(self):
        self.report = {}

    def __str__(self):
        return pformat(self.report)


class PlatformStatusReport(Report):
    def include_swarm_status(self, sw_status: SwarmStatus):
        self.report["swarm"] = sw_status.to_dict()


class ApplicationStatusReport(Report):
    def __init__(self, application: Application):
        super().__init__()
        self.report["executions"] = []
        self._app_to_dict(application)

    def _app_to_dict(self, application: Application):
        self.report.update(application.to_dict())

    def add_execution(self, execution: Execution):
        exrep = {
            'id': execution.id,
            'name': execution.name,
            'status': execution.status,
            'type': execution.type
        }
        if execution.time_scheduled is None:
            exrep['scheduled_at'] = None
        else:
            exrep['scheduled_at'] = execution.time_scheduled.timestamp()
        if execution.time_started is None:
            exrep['started_at'] = None
        else:
            exrep['started_at'] = execution.time_started.timestamp()
        if execution.time_finished is None:
            exrep['finished_at'] = None
        else:
            exrep['finished_at'] = execution.time_finished.timestamp()

        if isinstance(execution, SparkSubmitExecution):
            exrep["commandline"] = execution.commandline
            exrep["spark_opts"] = execution.spark_opts

        exrep["cluster"] = []

        if execution.cluster is None:
            self.report['executions'].append(exrep)
            return

        for c in execution.cluster.containers:
            cd = {
                'id': c.id,
                'docker_id': c.docker_id,
                'ip_address': c.ip_address,
                'name': c.readable_name,
                'proxies': []
            }
            for p in c.proxies:
                pd = {
                    'id': p.id,
                    'internal_url': p.internal_url,
                    'service_name': p.service_name,
                    'last_access': p.last_access.timestamp()
                }
                cd['proxies'].append(pd)
            exrep["cluster"].append(cd)
        self.report['executions'].append(exrep)
