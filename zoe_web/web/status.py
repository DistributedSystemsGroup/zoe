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

import zoe_lib.users as us
from flask import render_template, redirect, url_for, session

from zoe_web.web import web_bp


@web_bp.route('/status/platform')
def status_platform():
    user = us.user_get(session['user_id'])
    if user is None:
        return redirect(url_for('web.index'))
    platform_stats = di.platform_stats()

    template_vars = {
        "user_id": user.id,
        "platform": platform_stats
    }
    return render_template('platform_stats.html', **template_vars)
