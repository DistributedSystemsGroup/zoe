import logging
import requests

from zoe_observer.config import get_conf

log = logging.getLogger(__name__)


def _get_api_base_url():
    return 'http://' + get_conf().scheduler_address + ':' + get_conf().scheduler_port + '/api/0.5'


def _process_reply(request):
    status_code = request.status_code
    if status_code >= 400:
        reply = request.json()
        log.error(reply['message'])


def main_callback(event):
    log.debug(event)
    if event['status'] == "die":
        container_died(event['id'])


def container_died(docker_id: str):
    log.debug('A container died')
    # tell the scheduler via the rest api
    url = _get_api_base_url() + '/container/' + docker_id
    r = requests.delete(url, auth=('zoeadmin', get_conf().zoeadmin_password))
    _process_reply(r)
