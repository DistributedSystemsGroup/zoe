# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import smtplib
from email.mime.text import MIMEText
import logging

from jinja2 import Template

from zoe_master.state.execution import ExecutionState
from common.configuration import zoe_conf

log = logging.getLogger(__name__)

APP_FINISH_EMAIL_TEMPLATE = """Application {{ name }} has finished executing after {{ runtime }}.

At this URL you can download the execution logs: {{ log_url }}
"""


def generate_log_history_url(execution: ExecutionState) -> str:
    zoe_web_log_history_path = '/api/history/logs/'
    return 'http://' + zoe_conf().web_server_name + zoe_web_log_history_path + str(execution.id)


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


def notify_execution_finished(execution: ExecutionState):
    app = execution.application
    email = app.user.email

    template_vars = {
        'runtime': do_duration((execution.time_finished - execution.time_started).total_seconds()),
        'name': execution.name,
        'app_name': execution.application.description.name,
        'log_url': generate_log_history_url(execution)
    }
    subject = '[Zoe] Application execution {} finished'.format(execution.name)
    send_email(email, subject, APP_FINISH_EMAIL_TEMPLATE, template_vars)


def send_email(address, subject, template, template_vars):
    jinja_template = Template(template)
    body = jinja_template.render(template_vars)
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'noreply@bigfoot.eurecom.fr'
    msg['To'] = address
    s = smtplib.SMTP(zoe_conf().smtp_server)
    s.ehlo()
    s.starttls()
    s.login(zoe_conf().smtp_user, zoe_conf().smtp_password)
    s.send_message(msg)
    s.quit()
