import logging

from zoe_observer.config import get_conf
from zoe_lib.containers import ZoeContainerAPI

log = logging.getLogger(__name__)


def main_callback(event):
    log.debug(event)
    if event['status'] == "die":
        container_died(event['id'])


def container_died(zoe_id: int):
    log.debug('A container died')
    # tell the scheduler via the rest api
    cont_api = ZoeContainerAPI(get_conf().scheduler_url, 'zoeadmin', get_conf().zoeadmin_password)
    cont_api.died(zoe_id)
