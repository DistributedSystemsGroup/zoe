import smtplib
from email.mime.text import MIMEText
import logging

from jinja2 import Template

from zoe_scheduler.state.execution import SparkSubmitExecutionState, ExecutionState
from zoe_scheduler.urls import generate_log_history_url, generate_notebook_url
from common.configuration import zoeconf

log = logging.getLogger(__name__)

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


def notify_execution_finished(execution: SparkSubmitExecutionState):
    app = execution.application
    email = app.user.email

    template_vars = {
        'cmdline': execution.commandline,
        'runtime': do_duration((execution.time_finished - execution.time_started).total_seconds()),
        'name': execution.name,
        'app_name': execution.application.name,
        'log_url': generate_log_history_url(execution)
    }
    subject = '[Zoe] Spark execution {} finished'.format(execution.name)
    send_email(email, subject, APP_FINISH_EMAIL_TEMPLATE, template_vars)


def notify_notebook_notice(execution: ExecutionState):
    app = execution.application
    email = app.user.email

    subject = "[Zoe] Notebook termination warning"
    template_vars = {
        'grace_time': zoeconf().notebook_max_age_no_activity - zoeconf().notebook_warning_age_no_activity,
        'wrn_age': zoeconf().notebook_warning_age_no_activity,
        'nb_url': generate_notebook_url(execution)
    }
    send_email(email, subject, NOTEBOOK_WARNING_EMAIL_TEMPLATE, template_vars)


def notify_notebook_termination(execution: ExecutionState):
    app = execution.application
    email = app.user.email

    subject = "[Zoe] Notebook terminated"
    template_vars = {'max_age': zoeconf().notebook_max_age_no_activity}
    send_email(email, subject, NOTEBOOK_KILLED_EMAIL_TEMPLATE, template_vars)


def send_email(address, subject, template, template_vars):
    jinja_template = Template(template)
    body = jinja_template.render(template_vars)
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'noreply@bigfoot.eurecom.fr'
    msg['To'] = address
    s = smtplib.SMTP(zoeconf().smtp_server)
    s.ehlo()
    s.starttls()
    s.login(zoeconf().smtp_user, zoeconf().smtp_password)
    s.send_message(msg)
    s.quit()
