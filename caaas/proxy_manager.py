from caaas import CAaaState
from utils.config import get_proxy_base


def _generate_proxied_url(proxy_id):
    return get_proxy_base() + "/" + proxy_id


def get_container_addresses(container_id):
    state = CAaaState()
    proxy_list = state.get_proxies(container_id=container_id)
    urls = []
    for p in proxy_list:
        external_url = _generate_proxied_url(p["proxy_id"])
        urls.append((p["service_name"], external_url))
    return urls


def get_notebook_address(cluster_id):
    state = CAaaState()
    proxy_id = state.get_proxy_for_service(cluster_id, "notebook")
    return _generate_proxied_url(proxy_id)
