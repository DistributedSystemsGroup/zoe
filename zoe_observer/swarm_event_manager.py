import logging

from zoe_observer.config import get_conf
from zoe_lib.services import ZoeServiceAPI
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


def main_callback(event):
    log.debug(event)
    if event['Type'] != 'container':
        return

    try:
        if event['Actor']['Attributes']['zoe.deployment_name'] != get_conf().deployment_name:
            return
    except KeyError:
        return

    if event['Action'] == "die":
        try:
            service_name = event['Actor']['Attributes']['zoe.service.name']
            execution_name = event['Actor']['Attributes']['zoe.execution.name']
            container_died(service_name, execution_name)
        except KeyError:
            return


def container_died(service_name, execution_name):
    log.debug('A container died')
    # tell the master via the rest api
    cont_api = ZoeServiceAPI(get_conf().master_url, 'zoeadmin', get_conf().zoeadmin_password)
    try:
        cont_api.died(service_name, execution_name)
    except ZoeAPIException as e:
        if e.message != "No such service":
            log.exception('Error reporting a dead service')
