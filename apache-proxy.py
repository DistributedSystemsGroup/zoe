from jinja2 import Template
from hashlib import md5
from os import system
from time import sleep
from urllib.parse import urlparse

from caaas import CAaaState

OUTFILE = "/tmp/caaas-proxy.conf"

ENTRY_TEMPLATE = """
<Location /proxy/{{ proxy_id }}>
    ProxyHtmlEnable On
    ProxyHTMLExtended On
    ProxyPass {{ proxy_url }}
    ProxyPassReverse {{ proxy_url }}
    {% if proxy_type != "spark-notebook" %}
    ProxyHTMLURLMap ^/(.*)$ /proxy/{{ proxy_id }}/$1 RL
    {% endif %}
</Location>
{% if proxy_type == "spark-notebook" %}
<Location /proxy/{{ proxy_id }}/ws/>
    ProxyPass ws://{{ netloc }}/proxy/{{ proxy_id }}/ws/
</Location>
{% endif %}
"""


def get_proxy_entries():
    db = CAaaState()
    return db.get_all_proxy()


def generate_file(proxy_entries):
    output = ""
    jinja_template = Template(ENTRY_TEMPLATE)
    for proxy_id, proxy_url, proxy_type, cont_id in proxy_entries:
        netloc = urlparse(proxy_url)[1]
        jinja_dict = {
            "proxy_id": proxy_id,
            "proxy_url": proxy_url,
            "proxy_type": proxy_type,
            "netloc": netloc
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
