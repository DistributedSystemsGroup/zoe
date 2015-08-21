from datetime import datetime, timedelta
import time
from traceback import print_exc
import smtplib
from email.mime.text import MIMEText
import logging
log = logging.getLogger(__name__)

from jinja2 import Template

from caaas_web.config_parser import config
from caaas_web.proxy_manager import get_notebook_address
from caaas_web.sql import CAaaState
from caaas_web.swarm_manager import sm

APP_FINISH_EMAIL_TEMPLATE = """Application {{ name }} has finished executing after {{ runtime }}.

At this URL you can download the execution logs: {{ log_url }}
"""

NOTEBOOK_KILLED_EMAIL_TEMPLATE = """Your Spark notebook has not been used in the past {{ max_age }} hours and has been terminated."""

NOTEBOOK_WARNING_EMAIL_TEMPLATE = """Your Spark notebook has not been used in the past {{ wrn_age }} hours
and will be terminated unless you access it in the next {{ grace_time }} hours.

Notebook URL: {{ nb_url }}
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


def cleanup_task():
    ts = time.time()
    # noinspection PyBroadException
    try:
        clean_completed_apps()
        check_notebooks()
    except:
        print_exc()
    log.debug("Cleanup task completed in {:.3}s".format(time.time() - ts))


def check_notebooks():
    state = CAaaState()
    td = timedelta(hours=int(config.cleanup_notebooks_older_than))
    old_age = datetime.now() - td
    nb_too_old = state.get_old_spark_notebooks(old_age)
    for cluster_id in nb_too_old:
        user_id = state.get_cluster(cluster_id)["user_id"]
        sm.terminate_cluster(cluster_id)
        subject = "[CAaas] Notebook terminated"
        user_email = state.get_user_email(user_id)
        template_vars = {'max_age': config.cleanup_notebooks_older_than}
        send_email(user_email, subject, NOTEBOOK_KILLED_EMAIL_TEMPLATE, template_vars)

    td = timedelta(hours=int(config.cleanup_notebooks_warning))
    wrn_age = datetime.now() - td
    nb_wrn = state.get_old_spark_notebooks(wrn_age)
    for cluster_id in nb_wrn:
        user_id = state.get_cluster(cluster_id)["user_id"]
        subject = "[CAaas] Notebook termination advance warning"
        user_email = state.get_user_email(user_id)
        template_vars = {
            'grace_time': int(config.cleanup_notebooks_older_than) - int(config.cleanup_notebooks_warning),
            'wrn_age': config.cleanup_notebooks_warning,
            'nb_url': get_notebook_address(cluster_id)
        }
        send_email(user_email, subject, NOTEBOOK_WARNING_EMAIL_TEMPLATE, template_vars)


def app_cleanup(app_id, cluster_id):
    sm.save_logs(app_id, cluster_id)

    state = CAaaState()
    app = state.get_application(app_id)
    email = state.get_user_email(app["user_id"])
    template_vars = {
        'cmdline': app["cmd"],
        'runtime': do_duration((app["time_finished"] - app["time_started"]).total_seconds()),
        'name': app["execution_name"],
        'log_url': config.flask_base_url + "/api/{}/history/{}/logs".format(app["user_id"], app_id)
    }
    subject = '[CAaaS] Spark execution {} finished'.format(app["execution_name"])
    send_email(email, subject, APP_FINISH_EMAIL_TEMPLATE, template_vars)

    sm.terminate_cluster(cluster_id)


def send_email(address, subject, template, template_vars):
    jinja_template = Template(template)
    body = jinja_template.render(template_vars)
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'noreply@bigfoot.eurecom.fr'
    msg['To'] = address
    s = smtplib.SMTP(config.smtp_server)
    s.ehlo()
    s.starttls()
    s.login(config.smtp_user, config.smtp_pass)
    s.send_message(msg)
    s.quit()


def clean_completed_apps():
    state = CAaaState()
    cont_ids = state.get_submit_containers()
    for cont_id, cluster_id in cont_ids:
        if not sm.check_container_alive(cont_id):
            app_id = state.find_app_for_cluster(cluster_id)
            log.info("App {} needs to be cleaned up".format(app_id))
            state.application_finished(app_id)
            app_cleanup(app_id, cluster_id)
