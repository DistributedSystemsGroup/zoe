# Copyright (c) 2014 thkang2
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Jinja2 templating for Tornado, taken from https://github.com/thkang2/jinja_tornado"""

import json
import datetime
import logging

from jinja2 import Environment, FileSystemLoader, Markup, TemplateSyntaxError

from tornado.escape import squeeze, linkify, url_escape, xhtml_escape

import zoe_lib.config
import zoe_lib.version
from zoe_api.custom_request_handler import ZoeRequestHandler
from zoe_api.exceptions import ZoeAuthException

log = logging.getLogger(__name__)


class JinjaApp:
    """A Jinja2-capable Tornado application."""
    def __init__(self, application, jinja_options=None):
        self.application = application
        self.jinja_options = jinja_options
        self.init_app(application, jinja_options)

    @classmethod
    def init_app(cls, application, jinja_options=None):
        """Init the application."""
        app_settings = application.settings

        _loader = FileSystemLoader(
            app_settings.get('template_path', 'templates')
        )

        _jinja_config = {
            'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.with_'],
            'auto_reload': app_settings.get('autoreload', False),
            'loader': _loader,
            'cache_size': 50 if app_settings.get('compiled_template_cache', True) else 0,
            'autoescape': app_settings.get('autoescape', 'xhtml_escape') == "xhtml_escape"
        }

        _jinja_config.update(**(jinja_options or {}))
        environment = Environment(**_jinja_config)

        application.jinja_environment = environment
        app_settings['jinja_environment'] = environment
        environment.filters.update(tojson=tojson_filter, xhtml_escape=xhtml_escape, url_escape=url_escape, squeeze=squeeze, linkify=linkify)

        return environment


def dumps(obj, **kwargs):
    """Escape characters."""
    # https://github.com/mitsuhiko/flask/blob/master/flask/json.py
    return json.dumps(obj, **kwargs) \
        .replace(u'<', u'\\u003c') \
        .replace(u'>', u'\\u003e') \
        .replace(u'&', u'\\u0026') \
        .replace(u"'", u'\\u0027')


def tojson_filter(obj, **kwargs):
    """Filter for JSON output in templates."""
    # https://github.com/mitsuhiko/flask/blob/master/flask/json.py
    return Markup(dumps(obj, **kwargs))


class ZoeWebRequestHandler(ZoeRequestHandler):
    """RequestHandler class for Zoe Web interface."""

    def initialize(self, **kwargs):
        """Initialize the Jinja template system."""
        super().initialize(**kwargs)
        if 'jinja_environment' not in self.application.settings:
            raise RuntimeError("Needs jinja2 Environment. Initialize with JinjaApp.init_app first")
        else:
            self._jinja_env = self.application.settings['jinja_environment']

    def _render(self, template, **kwargs):
        """ todo: support multiple template preprocessors """

        ctx = {
            'request': self.request,
            'path_args': self.path_args,
            'path_kwargs': self.path_kwargs,
            'settings': self.application.settings,
            'reverse_url': self.application.reverse_url,
            'static_url': self.static_url,
            'xsrf_form_html': self.xsrf_form_html,
            'datetime': datetime,
            'locale': self.locale,
            'handler': self,
            'zoe_version': zoe_lib.version.ZOE_VERSION,
            'server_address': self.request.host,
        }

        try:
            ctx['user'] = super().get_current_user()
        except ZoeAuthException:
            pass

        ctx.update(kwargs)
        return template.render(ctx)

    def render(self, template_name, **kwargs):
        """ renders a template file. """
        template = self._jinja_env.get_template(template_name)
        try:
            html = self._render(template, **kwargs)
        except TemplateSyntaxError as e:
            self.error_page('Template syntax error at {}:{}:<br> {}'.format(e.name, e.lineno, e.message), 500)
            return
        except Exception as e:
            log.exception('Jinja2 exception while rendering the template {}'.format(template_name))
            self.error_page('Jinja2 template exception: {}'.format(e), 500)
            return
        self.finish(html)

    def render_string(self, source, **kwargs):
        """ renders a template source string. """
        template = self._jinja_env.from_string(source)
        return self._render(template, **kwargs)

    def get_current_user(self):
        """In case auth fails, redirect to login page."""
        try:
            user = super().get_current_user()
        except ZoeAuthException as e:
            with_gitlab_oauth = zoe_lib.config.get_conf().oauth_client_id != ''
            self.render('login.jinja2', error=e.message, with_gitlab_oauth=with_gitlab_oauth)
            return None
        return user

    def error_page(self, error_message: str, status: int = 400):
        """Generate an error page."""
        self.set_status(status)
        self.render('error.jinja2', error=error_message)
