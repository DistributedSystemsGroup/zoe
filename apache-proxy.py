from hashlib import md5
from os import system
from time import sleep
from urllib.parse import urlparse
import re
from datetime import datetime

from jinja2 import Template

from caaas.sql import CAaaState
from caaas.config_parser import config

LOOP_INTERVAL = 1  # seconds
ACCESS_TIME_REFRESH_INTERVAL = 60  # seconds

ENTRY_TEMPLATE = """
# CAaaS proxy entry for service {{ service_name }}
<Location /proxy/{{ proxy_id }}>
    ProxyHtmlEnable On
    ProxyHTMLExtended On
    ProxyPass {{ proxy_url }} retry=1
    ProxyPassReverse {{ proxy_url }}
    {% if service_name != "notebook" %}
    ProxyHTMLURLMap ^/(.*)$ /proxy/{{ proxy_id }}/$1 RL
    ProxyHTMLURLMap ^logPage(.*)$ /proxy/{{ proxy_id }}/logPage$1 RL
    ProxyHTMLURLMap ^app(.*)$ /proxy/{{ proxy_id }}/app$1 RL
    {% for node in nodes %}
    ProxyHTMLURLMap ^http://{{ node[0] }}(.*)$ /proxy/{{node[1]}}$1 RL
    {% endfor %}
    {% endif %}
</Location>
{% if service_name == "notebook" %}
<Location /proxy/{{ proxy_id }}/ws/>
    ProxyPass ws://{{ netloc }}/proxy/{{ proxy_id }}/ws/
</Location>
{% endif %}
"""


def get_proxy_entries():
    db = CAaaState()
    return db.get_proxies()


def generate_file(proxy_entries):
    output = ""
    jinja_template = Template(ENTRY_TEMPLATE)
    node_list = []
    for p in proxy_entries:
        netloc = urlparse(p["internal_url"])[1]
        node_list.append((netloc, p["id"]))
    for p in proxy_entries:
        netloc = urlparse(p["internal_url"])[1]
        jinja_dict = {
            "proxy_id": p["id"],
            "proxy_url": p["internal_url"],
            "service_name": p["service_name"],
            "netloc": netloc,
            "nodes": node_list
        }
        apache_entry = jinja_template.render(jinja_dict)
        output += apache_entry + "\n"
    return output


def check_difference(generated_file):
    m_new = md5()
    m_new.update(generated_file.encode('ascii'))
    m_old = md5()
    try:
        m_old.update(open(config.proxy_apache_config).read().encode('ascii'))
    except FileNotFoundError:
        return True
    return m_new.digest() != m_old.digest()


def commit_and_reload(generated_file):
    print("Apache config requires an update, committing and reloading")
    open(config.proxy_apache_config, "w").write(generated_file)
    system("sudo service apache2 reload")


def update_proxy():
    entries = get_proxy_entries()
    output = generate_file(entries)
    if check_difference(output):
        commit_and_reload(output)


def update_proxy_access_timestamps():
    regex = re.compile('[0-9.]+ - - \[(.*)\] "GET /proxy/([0-9a-z\-]+)/')
    log = open(config.proxy_apache_access_log, 'r')
    last_accesses = {}
    for line in log:
        match = re.match(regex, line)
        if match is not None:
            proxy_id = match.group(2)
            timestamp = datetime.strptime(match.group(1), "%d/%b/%Y:%H:%M:%S %z")
            last_accesses[proxy_id] = timestamp

    state = CAaaState()
    for proxy in state.get_proxies():
        proxy_id = proxy['id']
        if proxy_id in last_accesses:
            state.update_proxy_access(proxy_id, last_accesses[proxy_id])


if __name__ == "__main__":
    print("CAaaS Apache proxy synchronization starting")
    access_time_refresh_delay = ACCESS_TIME_REFRESH_INTERVAL
    while True:
        # print("Checking proxy entries...")
        update_proxy()
        # print("Checking for completed applications to clean up")
        sleep(LOOP_INTERVAL)
        access_time_refresh_delay -= LOOP_INTERVAL
        if access_time_refresh_delay <= 0:
            update_proxy_access_timestamps()
            access_time_refresh_delay = ACCESS_TIME_REFRESH_INTERVAL
