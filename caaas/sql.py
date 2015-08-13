import mysql.connector
import mysql.connector.cursor
import mysql.connector.errors

from caaas.config_parser import config


class CAaaState:
    def __init__(self):
        self.cnx = None

    def _reconnect(self):
        if self.cnx is not None:
            self.cnx.disconnect()
        db_config = {
            'user': config.db_user,
            'password': config.db_pass,
            'host': config.db_server,
            'database': config.db_db,
            'buffered': True
        }
        self.cnx = mysql.connector.connect(**db_config)

    def _get_cursor(self, dictionary=False) -> mysql.connector.cursor.MySQLCursor:
        try:
            cursor = self.cnx.cursor(dictionary=dictionary)
        except (mysql.connector.errors.OperationalError, AttributeError):
            self._reconnect()
            cursor = self.cnx.cursor(dictionary=dictionary)
        return cursor

    def _close_cursor(self, cursor):
        self.cnx.commit()
        cursor.close()

    def _check_user(self, username):
        cursor = self._get_cursor(dictionary=True)
        q = "SELECT id FROM users WHERE username=%s"

        cursor.execute(q, (username,))
        if cursor.rowcount == 0:
            self._close_cursor(cursor)
            return self._create_user(username)
        else:
            row = cursor.fetchone()
            self._close_cursor(cursor)
            return row["id"]

    def _create_user(self, username):
        cursor = self._get_cursor()
        q = "INSERT INTO users (username) VALUES (%s)"
        cursor.execute(q, (username,))
        user_id = cursor.lastrowid
        self._close_cursor(cursor)
        return user_id

    def get_user_id(self, username):
        return self._check_user(username)

    def get_user_email(self, user_id):
        cursor = self._get_cursor()
        q = "SELECT username FROM users WHERE id=%s"
        cursor.execute(q, (user_id,))
        row = cursor.fetchone()
        self._close_cursor(cursor)
        return row[0]

    def get_all_users(self):
        cursor = self._get_cursor()
        q = "SELECT id, username FROM users"

        user_list = []
        cursor.execute(q)
        for row in cursor:
            user_list.append(row)
        self._close_cursor(cursor)
        return user_list

    def count_apps_finished(self, user_id=None):
        cursor = self._get_cursor()
        if user_id is None:
            q = "SELECT COUNT(*) FROM applications WHERE time_finished IS NOT NULL"
            cursor.execute(q)
        else:
            q = "SELECT COUNT(*) FROM applications WHERE user_id=%s AND time_finished IS NOT NULL"
            cursor.execute(q, (user_id,))
        row = cursor.fetchone()
        self._close_cursor(cursor)
        return row[0]

    def count_clusters(self, user_id=None):
        cursor = self._get_cursor()
        if user_id is None:
            q = "SELECT COUNT(*) FROM clusters"
            cursor.execute(q)
        else:
            q = "SELECT COUNT(*) FROM clusters WHERE user_id=%s"
            cursor.execute(q, (user_id,))
        row = cursor.fetchone()
        self._close_cursor(cursor)
        return row[0]

    def count_containers(self, user_id=None, cluster_id=None):
        cursor = self._get_cursor()
        if user_id is None and cluster_id is None:
            q = "SELECT COUNT(*) FROM containers"
            cursor.execute(q)
        elif user_id is not None and cluster_id is None:
            q = "SELECT COUNT(*) FROM containers WHERE user_id=%s"
            cursor.execute(q, (user_id,))
        elif user_id is None and cluster_id is not None:
            q = "SELECT COUNT(*) FROM containers WHERE cluster_id=%s"
            cursor.execute(q, (cluster_id,))
        elif user_id is not None and cluster_id is not None:
            q = "SELECT COUNT(*) FROM containers WHERE user_id=%s AND cluster_id=%s"
            cursor.execute(q, (user_id, cluster_id))

        row = cursor.fetchone()
        self._close_cursor(cursor)
        return row[0]

    def get_notebook(self, user_id):
        cursor = self._get_cursor(dictionary=True)
        q = "SELECT id FROM clusters WHERE user_id=%s and name='notebook'"
        cursor.execute(q, (user_id,))
        if cursor.rowcount == 0:
            self._close_cursor(cursor)
            return None
        else:
            row = cursor.fetchone()
            self._close_cursor(cursor)
            return row["id"]

    def has_notebook(self, user_id):
        ret = self.get_notebook(user_id)
        return ret is not None

    def get_url_proxy(self, proxy_id):
        cursor = self._get_cursor()
        q = "SELECT internal_url FROM proxy WHERE proxy_id=%s"
        cursor.execute(q, (proxy_id,))
        if cursor.rowcount == 0:
            self._close_cursor(cursor)
            return None
        else:
            row = cursor.fetchone()
            self._close_cursor(cursor)
            return row[0]

    def get_proxy_for_service(self, cluster_id, service_name):
        cursor = self._get_cursor()
        q = "SELECT proxy_id FROM proxy WHERE cluster_id=%s AND service_name=%s"
        cursor.execute(q, (cluster_id, service_name))
        if cursor.rowcount == 0:
            self._close_cursor(cursor)
            return None
        else:
            row = cursor.fetchone()
            self._close_cursor(cursor)
            return row[0]

    def new_cluster(self, user_id, name):
        cursor = self._get_cursor()
        q = "INSERT INTO clusters (user_id, name) VALUES (%s, %s)"
        cursor.execute(q, (user_id, name))
        cluster_id = cursor.lastrowid
        self._close_cursor(cursor)
        return cluster_id

    def set_master_address(self, cluster_id, address):
        cursor = self._get_cursor()
        q = "UPDATE clusters SET master_address=%s WHERE id=%s"
        cursor.execute(q, (address, cluster_id))
        self._close_cursor(cursor)
        cursor.close()

    def new_container(self, cluster_id, user_id, docker_id, ip_address, contents):
        cursor = self._get_cursor()
        q = "INSERT INTO containers (user_id, cluster_id, docker_id, ip_address, contents) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(q, (user_id, cluster_id, docker_id, ip_address, contents))
        cont_id = cursor.lastrowid
        self._close_cursor(cursor)
        return cont_id

    def new_proxy_entry(self, proxy_id, cluster_id, address, service_name, container_id):
        cursor = self._get_cursor()
        q = "INSERT INTO proxy (proxy_id, internal_url, cluster_id, service_name, container_id)  VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(q, (proxy_id, address, cluster_id, service_name, container_id))
        self._close_cursor(cursor)
        return proxy_id

    def get_clusters(self, user_id=None):
        cursor = self._get_cursor(dictionary=True)
        res = {}
        if user_id is None:
            q = "SELECT id, user_id, master_address, name FROM clusters"
            cursor.execute(q)
        else:
            q = "SELECT id, user_id, master_address, name FROM clusters WHERE user_id=%s"
            cursor.execute(q, (user_id,))
        for row in cursor:
            res[str(row["id"])] = {
                "user_id": row["user_id"],
                "master_address": row["master_address"],
                "name": row["name"]
            }
        self._close_cursor(cursor)
        return res

    def get_cluster(self, cluster_id):
        cursor = self._get_cursor(dictionary=True)
        q = "SELECT * FROM clusters WHERE id=%s"
        cursor.execute(q, (cluster_id,))
        row = cursor.fetchone()
        res = dict(row)
        self._close_cursor(cursor)
        return res

    def get_containers(self, user_id=None, cluster_id=None):
        cursor = self._get_cursor(dictionary=True)
        res = {}
        if user_id is None and cluster_id is None:
            q = "SELECT id, docker_id, cluster_id, user_id, ip_address, contents FROM containers"
            cursor.execute(q)
        elif user_id is not None and cluster_id is None:
            q = "SELECT id, docker_id, cluster_id, user_id, ip_address, contents FROM containers WHERE user_id=%s"
            cursor.execute(q, (user_id,))
        elif user_id is None and cluster_id is not None:
            q = "SELECT id, docker_id, cluster_id, user_id, ip_address, contents FROM containers WHERE cluster_id=%s"
            cursor.execute(q, (cluster_id,))
        elif user_id is not None and cluster_id is not None:
            q = "SELECT id, docker_id, cluster_id, user_id, ip_address, contents FROM containers WHERE user_id=%s AND cluster_id=%s"
            cursor.execute(q, (user_id, cluster_id))

        for row in cursor:
            res[str(row["id"])] = {
                "docker_id": row["docker_id"],
                "cluster_id": row["cluster_id"],
                "user_id": row["user_id"],
                "ip_address": row["ip_address"],
                "contents": row["contents"],
            }
        self._close_cursor(cursor)
        return res

    def get_container(self, container_id):
        cursor = self._get_cursor(dictionary=True)
        res = {}
        q = "SELECT id, docker_id, cluster_id, user_id, ip_address, contents FROM containers WHERE id=%s"
        cursor.execute(q, (container_id,))

        for row in cursor:
            res = {
                "id": row["id"],
                "docker_id": row["docker_id"],
                "cluster_id": row["cluster_id"],
                "user_id": row["user_id"],
                "ip_address": row["ip_address"],
                "contents": row["contents"],
            }
        self._close_cursor(cursor)
        return res

    def get_submit_containers(self) -> (int, int):
        cursor = self._get_cursor(dictionary=True)
        res = []
        q = "SELECT id, cluster_id FROM containers WHERE contents='spark-submit'"
        cursor.execute(q)
        for row in cursor:
            res.append((row["id"], row["cluster_id"]))
        self._close_cursor(cursor)
        return res

    def get_proxies(self, cluster_id=None, container_id=None):
        cursor = self._get_cursor(dictionary=True)
        if cluster_id is None and container_id is None:
            q = "SELECT * FROM proxy"
            cursor.execute(q)
        elif container_id is not None:
            q = "SELECT * FROM proxy WHERE container_id=%s"
            cursor.execute(q, (container_id,))
        else:
            q = "SELECT * FROM proxy WHERE cluster_id=%s"
            cursor.execute(q, (cluster_id,))
        proxy_list = []
        for row in cursor:
            proxy_list.append(dict(row))
        self._close_cursor(cursor)
        return proxy_list

    def remove_proxy(self, container_id):
        cursor = self._get_cursor()
        q = "DELETE FROM proxy WHERE container_id=%s"
        cursor.execute(q, (container_id,))
        self._close_cursor(cursor)

    def remove_container(self, container_id):
        cursor = self._get_cursor()
        q = "DELETE FROM containers WHERE id=%s"
        cursor.execute(q, (container_id,))
        self._close_cursor(cursor)

    def remove_cluster(self, cluster_id):
        cursor = self._get_cursor()
        q = "DELETE FROM clusters WHERE id=%s"
        cursor.execute(q, (cluster_id,))
        self._close_cursor(cursor)

    def new_application(self, user_id: int, execution_name: str, spark_options: str, commandline: str) -> int:
        cursor = self._get_cursor()
        q = "INSERT INTO applications (execution_name, cmd, spark_options, user_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(q, (execution_name, commandline, spark_options, user_id))
        app_id = cursor.lastrowid
        self._close_cursor(cursor)
        return app_id

    def remove_oldest_application(self, user_id) -> str:
        cursor = self._get_cursor()
        q = "SELECT id FROM applications WHERE user_id=%s AND time_finished IS NOT NULL ORDER BY time_finished ASC LIMIT 1"
        cursor.execute(q, (user_id,))
        app_id = cursor.fetchone()[0]
        q = "DELETE FROM applications WHERE id=%s"
        cursor.execute(q, (app_id,))
        self._close_cursor(cursor)
        return app_id

    def application_ready(self, app_id):
        cursor = self._get_cursor()
        q = "UPDATE applications SET status='ready' WHERE id=%s"
        cursor.execute(q, (app_id,))
        self._close_cursor(cursor)

    def application_started(self, app_id, cluster_id):
        cursor = self._get_cursor()
        q = "UPDATE applications SET cluster_id=%s, time_started=CURRENT_TIMESTAMP, status='running' WHERE id=%s"
        cursor.execute(q, (cluster_id, app_id))
        self._close_cursor(cursor)

    def application_killed(self, app_id):
        cursor = self._get_cursor()
        q = "UPDATE applications SET time_finished=CURRENT_TIMESTAMP, status='killed' WHERE id=%s"
        cursor.execute(q, (app_id,))
        self._close_cursor(cursor)

    def application_finished(self, app_id):
        cursor = self._get_cursor()
        q = "UPDATE applications SET time_finished=CURRENT_TIMESTAMP, status='finished' WHERE id=%s"
        cursor.execute(q, (app_id,))
        self._close_cursor(cursor)

    def get_applications(self, user_id=None) -> dict:
        cursor = self._get_cursor(dictionary=True)
        if user_id is None:
            q = "SELECT * FROM applications"
            cursor.execute(q)
        else:
            q = "SELECT * FROM applications WHERE user_id=%s"
            cursor.execute(q, (user_id,))
        res = []
        for row in cursor:
            res.append((dict(row)))
        self._close_cursor(cursor)
        return res

    def get_application(self, app_id: int) -> dict:
        cursor = self._get_cursor(dictionary=True)
        q = "SELECT * FROM applications WHERE id=%s"
        cursor.execute(q, (app_id,))

        res = dict(cursor.fetchone())
        self._close_cursor(cursor)
        return res

    def find_app_for_cluster(self, cluster_id: int):
        cursor = self._get_cursor()
        q = "SELECT id FROM applications WHERE cluster_id=%s"
        cursor.execute(q, (cluster_id,))
        if cursor.rowcount > 0:
            res = cursor.fetchone()[0]
        else:
            res = None
        self._close_cursor(cursor)
        return res

    def update_proxy_access(self, proxy_id, access_ts):
        cursor = self._get_cursor()
        q = "UPDATE proxy SET last_access=%s WHERE proxy_id=%s"
        cursor.execute(q, (access_ts, proxy_id))
        self._close_cursor(cursor)

    def get_old_spark_notebooks(self, older_than):
        cursor = self._get_cursor()
        q = "SELECT cluster_id FROM proxy WHERE service_name='notebook' AND last_access < %s"
        cursor.execute(q, (older_than,))
        ret = [row[0] for row in cursor]
        self._close_cursor(cursor)
        return ret
