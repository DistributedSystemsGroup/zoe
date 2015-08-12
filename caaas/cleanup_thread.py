import threading
import time
import smtplib
from email.mime.text import MIMEText
from jinja2 import Template

from caaas import CAaaState, sm
from utils import config

EMAIL_TEMPLATE = """Application {{ name }} has finished executing after {{ runtime }}.

At this URL you can download the execution logs: {{ log_url }}
"""


def do_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    tokens = []
    if d > 1:
        tokens.append('{d:.0f} days')
    elif d:
        tokens.append('{d:.0f} day')
    if h > 1:
        tokens.append('{h:.0f} hours')
    elif h:
        tokens.append('{h:.0f} hour')
    if m > 1:
        tokens.append('{m:.0f} minutes')
    elif m:
        tokens.append('{m:.0f} minute')
    if s > 1:
        tokens.append('{s:.0f} seconds')
    elif s:
        tokens.append('{s:.0f} second')
    template = ', '.join(tokens)
    return template.format(d=d, h=h, m=m, s=s)


def start_cleanup_thread():
    th = threading.Thread(target=_loop)
    th.daemon = True
    th.start()


def _loop():
    while True:
        clean_completed_apps()
        time.sleep(config.get_cleanup_interval())


def app_cleanup(app_id, cluster_id):
    sm.save_logs(app_id, cluster_id)
    send_email(app_id)
    sm.terminate_cluster(cluster_id)


def send_email(app_id):
    state = CAaaState()
    app = state.get_application(app_id)
    username = state.get_user_email(app["user_id"])
    jinja_template = Template(EMAIL_TEMPLATE)
    body = jinja_template.render({
        'cmdline': app["cmd"],
        'runtime': do_duration((app["time_finished"] - app["time_started"]).total_seconds()),
        'name': app["execution_name"],
        'log_url': config.get_flask_server_url() + '/api/' + username + "/history/" + str(app_id) + "/logs"
    })
    msg = MIMEText(body)
    msg['Subject'] = '[CAaaS] Spark execution {} finished'.format(app["execution_name"])
    msg['From'] = 'noreply@bigfoot.eurecom.fr'
    msg['To'] = state.get_user_email(app["user_id"])
    mail_server = config.get_smtp_info()
    s = smtplib.SMTP(mail_server["server"])
    s.ehlo()
    s.starttls()
    s.login(mail_server["user"], mail_server["pass"])
    s.send_message(msg)
    s.quit()


def clean_completed_apps():
    state = CAaaState()
    cont_ids = state.get_submit_containers()
    for cont_id, cluster_id in cont_ids:
        if not sm.check_container_alive(cont_id):
            print("Found an app to cleanup")
            app_id = state.find_app_for_cluster(cluster_id)
            state.application_finished(app_id)
            app_cleanup(app_id, cluster_id)
