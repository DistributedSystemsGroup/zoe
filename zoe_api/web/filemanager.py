# Copyright (c) 2017, Daniele Venzano
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

"""A simple file manager to browse the user's workspace."""

import logging
import os
import shutil

import magic
import tornado.web
import tornado.websocket
import tornado.escape

from zoe_lib.workspace.filesystem import ZoeFSWorkspace
from zoe_api.web.utils import get_auth, catch_exceptions
from zoe_api.web.custom_request_handler import ZoeRequestHandler


ACTIONS = ['chdir', 'list_dir', 'create_dir', 'create_file', 'update_perms', 'update_buffer', 'paste_files', 'remove_files']

log = logging.getLogger(__name__)


#class Buffer(object):
#    """Storing some useful data"""
#
#    current_dir = get_conf().workspace_base_path
#    file_buffer = {'action': '', 'files': []}


class HandleAction:
    """
    Handling action.
    Attributes:
        data: some data for action.
    """

    def __init__(self, data, uid):
        self.data = data
        self.uid = uid
        self.workspace = ZoeFSWorkspace()

    def run(self):
        """
        Run action. Calls internal methods (started with underscore) to get
        result
        :return:
        """
        action = getattr(HandleAction(self.data, self.uid), '_' + self.data['do'])
        log.debug('Running action {}'.format(self.data['do']))
        result = {'action': self.data['do']}
        response = action()
        if 'exception' in response:
            result['exception'] = response['exception']
        else:
            result['response'] = response['response']
        return result

    def _chdir(self):
        """
        Change current directory
        :return:
        """
        if not all([item in self.data for item in ['path', 'name']]):
            return {'exception': 'Not enough data'}
        if self.data['path'] == '':
            self.data['path'] = self.workspace.get_path(self.uid)
        path = os.path.normpath(
            os.path.join(self.data['path'], self.data['name'])
        )
        if not path.startswith(self.workspace.get_path(self.uid)):
            path = self.workspace.get_path(self.uid)
        return {'response': {'result': path}}

    def _list_dir(self):
        """
        Show directory contents.
        :return:
        """
        log.debug('listdir for path {}'.format(self.data['path']))
        path = self.data['path']
        dir_model = DirectoryModel(path)
        try:
            files = dir_model.list_files()
        except (OSError, PermissionError) as e:
            return {'response': {'error': e.strerror, 'dir': path}}
        return {'response': {'files': files, 'dir': path}}

    def _create_dir(self):
        """
        Create new directory
        :return:
        """
        if 'name' not in self.data:
            return {'exception': 'Not enough data'}
        dir_model = DirectoryModel(Buffer.current_dir)
        try:
            result = dir_model.create(os.path.basename(self.data['name']))
        except IOError as e:
            error = e.strerror or str(e)
            return {'response': {'error': error}}
        return {'response': {'result': result}}

    def _update_buffer(self):
        """
        Update buffer (cut, copy, remove)
        :return:
        """
        if not all([item in self.data for item in ['files', 'action']]):
            return {'exception': 'Not enough data'}
        Buffer.file_buffer['files'] = [
            os.path.join(
                Buffer.current_dir, str(f)
            ) for f in self.data['files']
        ]
        Buffer.file_buffer['action'] = self.data['action']
        return {
            'response': {
                'result': len(Buffer.file_buffer['files']),
                'action': self.data['action']
            }
        }

    def _paste_files(self):
        """
        Paste files
        :return:
        """
        action = Buffer.file_buffer['action']
        files = Buffer.file_buffer['files']
        destination = Buffer.current_dir
        if action == 'cut':
            result = BatchActions.move(files, destination)
            Buffer.file_buffer = {'action': '', 'files': []}
        elif action == 'copy':
            result = BatchActions.copy(files, destination)
        else:
            return {'response': {'error': 'Cut and copy only'}}
        return {'response': {'result': result, 'action': action}}

    def _remove_files(self):
        """
        Remove files
        :return:
        """
        action = Buffer.file_buffer['action']
        files = Buffer.file_buffer['files']
        if action != 'remove':
            return {'response': {'error': 'Wrong action'}}
        result = BatchActions.remove(files)
        Buffer.file_buffer = {'action': '', 'files': []}
        return {'response': {'result': result}}

    def _update_perms(self):
        """
        Update file permissions (chmod)
        :return:
        """
        result = BatchActions.chmod(
            self.data['files'], self.data['mode'], self.data['recursive']
        )
        return {'response': {'result': result}}

    def _pwd(self):
        """
        Returns current directory
        :return:
        """
        result = Buffer.current_dir
        return {'response': {'result': result}}


class FileListHandler(ZoeRequestHandler):
    """File list."""

    @catch_exceptions
    def get(self):
        uid, role = get_auth(self)
        if uid is None:
            return self.redirect(self.get_argument('next', u'/login'))
        template_vars = {
            "uid": uid,
            "role": role
        }
        self.render('filemanager/file_list.html', **template_vars)


class UploadHandler(ZoeRequestHandler):
    """Upload file. Big files may eat much memory."""

    @catch_exceptions
    def get(self):
        self.render('upload.html')

    @catch_exceptions
    def post(self):
        try:
            new_file = self.request.files['uploadFile'][0]
            file_name = os.path.join(Buffer.current_dir, os.path.basename(new_file['filename']))
            with open(file_name, 'wb') as f:
                f.write(new_file['body'])
            response = 'File uploaded successfully'
        except KeyError:
            response = 'No file selected'
        except IOError as e:
            response = e.strerror
        self.render('upload.html', response=response)


class DownloadHandler(ZoeRequestHandler):
    """
    Download file. Can send big files without memory leak. By default, buffer
    size equals 1Mb
    """

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self, path):
        self.buffer_size = 1048576
        path = '/' + path
        if os.path.exists(path) and os.path.isfile(path):
            try:
                mime = magic.from_file(path)
            except magic.MagicException:
                mime = 'application/octet-stream'
            self.set_header("Content-Type", mime)
            self.set_header(
                "Content-Disposition", "attachment; filename={}".format(
                    os.path.basename(path)
                )
            )
            self.set_header("Content-Length", os.path.getsize(path))
            self.file = open(path, 'rb')
            self.send_file()
        else:
            self.send_error(404)

    def send_file(self):
        data = self.file.read(self.buffer_size)
        if not data:
            self.finish()
            self.file.close()
            return
        self.write(data)
        self.flush(callback=self.send_file)


class MainWsHandler(tornado.websocket.WebSocketHandler):
    """
    Websocket handler. Receives and checks action
    """
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize()
        self.api_endpoint = kwargs['api_endpoint']
        self.uid = None
        self.role = None

    def open(self):
        uid, role = get_auth(self)
        if uid is None:
            self.close(401, "Unauthorized")
        else:
            self.uid = uid
            self.role = role

    def on_message(self, message):
        try:
            data = tornado.escape.json_decode(message)
        except ValueError:
            self.write_message(tornado.escape.json_encode(
                {'exception': "Invalid JSON data"})
            )
            return
        if 'do' not in data:
            self.write_message(tornado.escape.json_encode(
                {'exception': "No action"})
            )
            return
        if data['do'] not in ACTIONS:
            self.write_message(tornado.escape.json_encode(
                {'exception': "Unknown action"})
            )
            return
        action = HandleAction(data, self.uid)
        result = action.run()
        self.write_message(tornado.escape.json_encode(result))


class BatchActions(object):
    """Some batch operations."""

    @staticmethod
    def move(files, path):
        successfully_moved = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                shutil.move(f, os.path.join(path, file_name))
                successfully_moved += 1
            except OSError:
                continue

        return successfully_moved

    @staticmethod
    def copy(files, path):
        successfully_copied = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                shutil.copy(f, os.path.join(path, file_name))
                successfully_copied += 1
            except OSError:
                continue

        return successfully_copied

    @staticmethod
    def remove(files):
        successfully_removed = 0
        for f in files:
            try:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)
                successfully_removed += 1
            except OSError:
                continue
        return successfully_removed

    @staticmethod
    def chmod(files, mode, recursive=False):
        successful_chmod = 0
        for f in files:
            if os.path.isdir(f):
                if recursive:
                    for path, dirs, _files in os.walk(f):
                        for _dir in dirs + _files:
                            try:
                                os.chmod(os.path.join(path, _dir), mode)
                                successful_chmod += 1
                            except OSError:
                                continue
                else:
                    try:
                        os.chmod(f, mode)
                        successful_chmod += 1
                    except OSError:
                        pass
            else:
                try:
                    os.chmod(f, mode)
                    successful_chmod += 1
                except OSError:
                    pass

        return successful_chmod


class DirectoryModel(object):
    """Directory model
    Attributes:
        current_dir: current working directory.
    """

    def __init__(self, current_dir):
        self.current_dir = current_dir

    def create(self, name):
        """
        Create new directory in current_dir
        :param name: directory name
        :return:
        """
        path = os.path.join(self.current_dir, name)
        if os.path.exists(path):
            raise IOError('Directory already exists')
        os.mkdir(path)
        return True

    def remove(self, name):
        """
        Remove directory in current_dir
        :param name: directory name
        :return:
        """
        os.rmdir(os.path.join(self.current_dir, name))
        return True

    def list_files(self):
        """
        Return list of files from current_dir
        :return:
        """
        files = os.listdir(self.current_dir)
        result = []
        if not files:
            return result

        file_model = FileModel(self.current_dir)
        for f in files:
            file_info = file_model.info(f)
            result.append(file_info)

        return result

    def get_size(self):
        """
        Get current_dir contents size
        :return:
        """
        dir_size = 0
        for path, dirs, files in os.walk(self.current_dir):
            for f in files:
                dir_size += os.path.getsize(os.path.join(path, f))

        return dir_size

    def chmod_dir(self, mode, recursive=False):
        """
        Change current_dir permissions
        :param mode: directory mode
        :param recursive: recursive change
        :return:
        """
        successful_chmod = 0
        if recursive:
            for path, dirs, files in os.walk(self.current_dir):
                for _dir in dirs:
                    os.chmod(os.path.join(path, _dir), mode)
                    successful_chmod += 1
                for f in files:
                    os.chmod(os.path.join(path, f), mode)
                    successful_chmod += 1
        else:
            os.chmod(self.current_dir, mode=mode)
            successful_chmod += 1

        return successful_chmod


class FileModel(object):
    """
    File model
    Attributes:
        current_dir: current working directory.
    """

    def __init__(self, current_dir):
        self.current_dir = current_dir

    def create(self, name):
        """
        Create new file in current_dir. May raise IOError if file exists
        :param name:
        :return:
        """
        file_path = os.path.join(self.current_dir, name)
        if os.path.exists(file_path):
            raise IOError('File already exists')
        open(file_path, 'a').close()
        return True

    def remove(self, name):
        """
        Remove file from current_dir
        :param name:
        :return:
        """
        os.remove(os.path.join(self.current_dir, name))
        return True

    def info(self, name):
        """
        Get file info from current_dir. Returns list
        :param name:
        :return:
        """
        target_inode = os.path.join(self.current_dir, name)
        stat_data = os.stat(target_inode)
        if not os.path.isdir(target_inode):
            try:

                mime_type = magic.from_file(target_inode, mime=True)
            except magic.MagicException:
                mime_type = 'application/octet-stream'
        else:
            mime_type = 'inode/directory'
        file_info = {
            'name': name,
            'path': self.current_dir,
            'mime': mime_type,
            'type': mime_type.replace('/', '-'),
            'size': stat_data.st_size,
            'mode': format(stat_data.st_mode & 0o777, 'o'),
            'owner_id': stat_data.st_uid,
            'group_id': stat_data.st_gid
        }
        if mime_type == 'inode/symlink':
            file_info['real_path'] = os.path.realpath(target_inode)
            file_info['real_mime'] = magic.from_file(
                file_info['real_path'], mime=True
            ).decode()
            file_info['real_type'] = file_info['real_mime'].replace('/', '-')
        return file_info

    def chmod_file(self, name, mode):
        """
        Change file permissions
        :param name:
        :param mode:
        :return:
        """
        os.chmod(os.path.join(self.current_dir, name), mode)
        return True
