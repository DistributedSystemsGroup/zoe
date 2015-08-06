from jinja2 import Template
from hashlib import md5
from os import system
from time import sleep
from urllib.parse import urlparse

from caaas import CAaaState

OUTFILE = "/tmp/caaas-proxy.conf"

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
        node_list.append((netloc, p["proxy_id"]))
    for p in proxy_entries:
        netloc = urlparse(p["internal_url"])[1]
        jinja_dict = {
            "proxy_id": p["proxy_id"],
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
        m_old.update(open(OUTFILE).read().encode('ascii'))
    except FileNotFoundError:
        return True
    return m_new.digest() != m_old.digest()


def commit_and_reload(generated_file):
    print("Apache config requires an update, committing and reloading")
    open(OUTFILE, "w").write(generated_file)
    system("sudo service apache2 reload")


if __name__ == "__main__":
    print("CAaaS Apache proxy synchronizer starting")

    while True:
        print("Looping...")
        entries = get_proxy_entries()
        print(entries)
        output = generate_file(entries)
        if check_difference(output):
            commit_and_reload(output)
        sleep(1)
