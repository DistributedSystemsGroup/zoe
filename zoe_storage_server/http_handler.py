import cgi
import http.server

from zoe_storage_server.object_storage import ZoePersistentObjectStore


class ZoeObjectStoreHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    This class extends the BaseHTTPRequestHandler from the Python library to provide an HTTP interface to the ZoePersistentObjectStore.
    """

    def _read_request(self):
        zos = ZoePersistentObjectStore()
        req = self.path.split("/")[1:]
        try:
            obj_type = req[0]
            obj_id = int(req[1])
        except ValueError:
            self.send_error(400, "ID should be a number")
            return None
        except IndexError:
            self.send_error(400, "Malformed URL")
            return None

        if obj_type == "apps":
            fdata = zos.application_data_download(obj_id)
        elif obj_type == "logs":
            fdata = zos.logs_archive_download(obj_id)
        else:
            self.send_error(400, "Unknown object type")
            return None

        if fdata is None:
            self.send_error(404, "Object not found")
            return None

        self.send_response(200)
        self.send_header("Content-type", "application/zip")
        self.send_header("Content-Length", str(len(fdata)))
        self.end_headers()
        return fdata

    def do_HEAD(self):
        self._read_request()

    def do_GET(self):
        fdata = self._read_request()
        if fdata is not None:
            self.wfile.write(fdata)

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get_content_type())
        if ctype == 'multipart/form-data':
            fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        else:
            self.send_error(400, "Expected form-data POST request")
            return

        zos = ZoePersistentObjectStore()
        req = self.path.split("/")[1:]
        try:
            obj_type = req[0]
            obj_id = int(req[1])
        except ValueError:
            self.send_error(400, "ID should be a number")
            return None
        except IndexError:
            self.send_error(400, "Malformed URL")
            return None
        if obj_type == "apps":
            zos.application_data_upload(obj_id, fs['file'].file)
        elif obj_type == "logs":
            zos.logs_archive_upload(obj_id, fs['file'].file)
        else:
            self.send_error(400, "Unknown object type")
            return None

        self.send_response(200, "Object saved")
        self.end_headers()

    def do_DELETE(self):
        zos = ZoePersistentObjectStore()
        req = self.path.split("/")[1:]
        try:
            obj_type = req[0]
            obj_id = int(req[1])
        except ValueError:
            self.send_error(400, "ID should be a number")
            return None
        except IndexError:
            self.send_error(400, "Malformed URL")
            return None
        if obj_type == "apps":
            zos.application_data_delete(obj_id)
        elif obj_type == "logs":
            zos.logs_archive_delete(obj_id)
        else:
            self.send_error(400, "Unknown object type")
            return None

        self.send_response(200, "Object saved")
        self.end_headers()
