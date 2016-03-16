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

from zoe_lib.configargparse import ArgumentParser, Namespace

config_paths = [
    'zoe-web.conf',
    '/etc/zoe/zoe-web.conf'
]

_conf = None


def load_configuration():
    global _conf
    argparser = ArgumentParser(description="Zoe Web interface: Container Analytics as a Service web component",
                               default_config_files=config_paths,
                               auto_env_var_prefix="ZOE_WEB_",
                               args_for_setting_config_path=["--config"],
                               args_for_writing_out_config_file=["--write-config"])
    argparser.add_argument('--debug', action='store_true', help='Enable debug output')
    argparser.add_argument('--listen-address', type=str, help='Address to listen to for incoming connections', default="0.0.0.0")
    argparser.add_argument('--listen-port', type=int, help='Port to listen to for incoming connections', default=5001)
    argparser.add_argument('--zoe-url', help='URL of the Zoe master process', default='http://127.0.0.1:4850')
    argparser.add_argument('--cookie-secret', help='key used to encrypt cookies', default="hr4h3H'kmn F8fz/;CJN5a!")

    opts = argparser.parse_args()
    if opts.debug:
        argparser.print_values()
    _conf = opts


def get_conf() -> Namespace:
    return _conf
