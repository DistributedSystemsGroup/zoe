from zoe_scheduler.state import AlchemySession
from zoe_scheduler.state.application import ApplicationState
from zoe_scheduler.state.execution import ExecutionState
from zoe_scheduler.state.proxy import ProxyState
from common.configuration import zoeconf


def generate_log_history_url(execution: ExecutionState) -> str:
    zoe_web_log_history_path = '/api/history/logs/'
    return 'http://' + zoeconf().web_server_name + zoe_web_log_history_path + str(execution.id)


def generate_notebook_url(execution: ExecutionState) -> str:
    state = AlchemySession()
    c = execution.find_container("spark-notebook")
    pr = state.query(ProxyState).filter_by(container_id=c.id, service_name="Spark Notebook interface").one()
    return 'http://' + zoeconf().web_server_name + zoeconf().proxy_path_url_prefix + '/{}'.format(pr.id)


def generate_application_binary_url(application: ApplicationState) -> str:
    return 'http://' + zoeconf().web_server_name + '/api/applications/download/{}'.format(application.id)
