from zoe_web.sql import CAaaState
from zoe_web.config_parser import config


def _generate_proxied_url(proxy_id):
    if proxy_id is not None:
        return config.proxy_base_url + "/" + proxy_id
    else:
        return None


def get_container_addresses(container_id):
    state = CAaaState()
    proxy_list = state.get_proxies(container_id=container_id)
    urls = []
    for p in proxy_list:
        external_url = _generate_proxied_url(p["id"])
        urls.append((p["service_name"], external_url))
    return urls


def get_notebook_address(cluster_id):
    state = CAaaState()
    proxy_id = state.get_proxy_for_service(cluster_id, "notebook")
    return _generate_proxied_url(proxy_id)
