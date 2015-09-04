from common.state.execution import Execution
from common.state import Proxy, AlchemySession
from common.configuration import conf


def generate_log_history_url(execution: Execution) -> str:
    zoe_web_log_history_path = '/api/history/logs/'
    return 'http://' + conf['web_server_name'] + zoe_web_log_history_path + str(execution.id)


def generate_notebook_url(execution: Execution) -> str:
    state = AlchemySession()
    c = execution.find_container("spark-notebook")
    pr = state.query(Proxy).filter_by(container_id=c.id, service_name="Spark Notebook interface").one()
    return 'http://' + conf['web_server_name'] + conf['proxy_path_prefix'] + '/{}'.format(pr.id)
