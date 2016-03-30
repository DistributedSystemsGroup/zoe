import logging

from zoe_observer.config import get_conf
from zoe_lib.services import ZoeServiceAPI
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


def main_callback(event):
    if event['Type'] != 'container':
        return

    try:
        if event['Actor']['Attributes']['zoe.deployment_name'] != get_conf().deployment_name:
            return
    except KeyError:
        return

    log.debug(event)

    if event['Action'] == "die":
        try:
            service_id = event['Actor']['Attributes']['zoe.service.id']
            container_died(service_id)
        except KeyError:
            return


def container_died(service_id):
    log.debug('A container died')
    # tell the master via the rest api
    cont_api = ZoeServiceAPI(get_conf().master_url, 'zoeadmin', get_conf().zoeadmin_password)
    try:
        cont_api.died(service_id)
    except ZoeAPIException as e:
        if e.message != "No such service":
            log.exception('Error reporting a dead service')
