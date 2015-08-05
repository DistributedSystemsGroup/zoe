import mysql.connector
from hashlib import md5


class CAaaSSQL:
    def __init__(self):
        self.cnx = None

    def connect(self, user, passw, server, dbname):
        assert self.cnx is None
        self.cnx = mysql.connector.connect(user=user, password=passw, host=server, database=dbname, buffered=True)

    def _check_user(self, username):
        cursor = self.cnx.cursor(dictionary=True)
        q = "SELECT id FROM users WHERE username=%s"

        cursor.execute(q, (username,))
        if cursor.rowcount == 0:
            self.cnx.commit()
            cursor.close()
            return self._create_user(username)
        else:
            row = cursor.fetchone()
            self.cnx.commit()
            cursor.close()
            return row["id"]

    def _create_user(self, username):
        cursor = self.cnx.cursor()
        q = "INSERT INTO users (username) VALUES (%s)"
        cursor.execute(q, (username,))
        user_id = cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return user_id

    def get_user_id(self, username):
        return self._check_user(username)

    def get_all_users(self):
        cursor = self.cnx.cursor()
        q = "SELECT id, username FROM users"

        user_list = []
        cursor.execute(q)
        for row in cursor:
            user_list.append(row)
        self.cnx.commit()
        cursor.close()
        return user_list

    def count_clusters(self, user_id=None):
        cursor = self.cnx.cursor()
        if user_id is None:
            q = "SELECT COUNT(*) FROM clusters"
            cursor.execute(q)
        else:
            q = "SELECT COUNT(*) FROM clusters WHERE user_id=%s"
            cursor.execute(q, (user_id,))
        row = cursor.fetchone()
        self.cnx.commit()
        cursor.close()
        return row[0]

    def count_containers(self, user_id=None, cluster_id=None):
        cursor = self.cnx.cursor()
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
        self.cnx.commit()
        cursor.close()
        return row[0]

    def get_notebook(self, user_id):
        cursor = self.cnx.cursor(dictionary=True)
        q = "SELECT * FROM notebooks WHERE user_id=%s"
        cursor.execute(q, (user_id,))
        if cursor.rowcount == 0:
            self.cnx.commit()
            cursor.close()
            return None
        else:
            row = cursor.fetchone()
            self.cnx.commit()
            cursor.close()
            return row

    def has_notebook(self, user_id):
        ret = self.get_notebook(user_id)
        return ret is not None

    def get_url_proxy(self, proxy_id):
        cursor = self.cnx.cursor()
        q = "SELECT url FROM proxy WHERE proxy_id=%s"
        cursor.execute(q, (proxy_id,))
        if cursor.rowcount == 0:
            self.cnx.commit()
            cursor.close()
            return None
        else:
            row = cursor.fetchone()
            self.cnx.commit()
            cursor.close()
            return row[0]

    def get_all_proxy(self):
        cursor = self.cnx.cursor()
        q = "SELECT proxy_id, url, proxy_type, container_id FROM proxy"
        cursor.execute(q)
        proxy_list = []
        for proxy_id, url, proxy_type, container_id in cursor:
            proxy_list.append((proxy_id, url, proxy_type, container_id))
        self.cnx.commit()
        cursor.close()
        return proxy_list

    def new_cluster(self, user_id, name):
        cursor = self.cnx.cursor()
        q = "INSERT INTO clusters (user_id, name) VALUES (%s, %s)"
        cursor.execute(q, (user_id, name))
        cluster_id = cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return cluster_id

    def set_master_address(self, cluster_id, address):
        cursor = self.cnx.cursor()
        q = "UPDATE clusters SET master_address=%s WHERE clusters.id=%s"
        print(address, cluster_id)
        cursor.execute(q, (address, cluster_id))
        self.cnx.commit()
        cursor.close()

    def new_container(self, cluster_id, user_id, docker_id, ip_address, contents):
        cursor = self.cnx.cursor()
        q = "INSERT INTO containers (user_id, cluster_id, docker_id, ip_address, contents) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(q, (user_id, cluster_id, docker_id, ip_address, contents))
        cont_id = cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return cont_id

    def new_proxy_entry(self, proxy_id, cluster_id, address, proxy_type, container_id):
        cursor = self.cnx.cursor()
        q = "INSERT INTO proxy (proxy_id, url, cluster_id, proxy_type, container_id)  VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(q, (proxy_id, address, cluster_id, proxy_type, container_id))
        self.cnx.commit()
        cursor.close()
        return proxy_id

    def new_notebook(self, cluster_id, address, user_id, container_id):
        cursor = self.cnx.cursor()
        q = "INSERT INTO notebooks (cluster_id, address, user_id, container_id)  VALUES (%s, %s, %s, %s)"
        cursor.execute(q, (cluster_id, address, user_id, container_id))
        nb_id = cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return nb_id

    def get_clusters(self, user_id=None):
        cursor = self.cnx.cursor(dictionary=True)
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
        self.cnx.commit()
        cursor.close()
        return res

    def get_containers(self, user_id=None, cluster_id=None):
        cursor = self.cnx.cursor(dictionary=True)
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
        self.cnx.commit()
        cursor.close()
        return res

    def remove_proxy(self, container_id):
        cursor = self.cnx.cursor()
        q = "DELETE FROM proxy WHERE container_id=%s"
        cursor.execute(q, (container_id,))
        self.cnx.commit()
        cursor.close()

    def remove_notebook(self, container_id):
        cursor = self.cnx.cursor()
        q = "DELETE FROM notebooks WHERE container_id=%s"
        cursor.execute(q, (container_id,))
        self.cnx.commit()
        cursor.close()

    def remove_container(self, container_id):
        cursor = self.cnx.cursor()
        q = "DELETE FROM containers WHERE id=%s"
        cursor.execute(q, (container_id,))
        self.cnx.commit()
        cursor.close()

    def remove_cluster(self, cluster_id):
        cursor = self.cnx.cursor()
        q = "DELETE FROM clusters WHERE id=%s"
        cursor.execute(q, (cluster_id,))
        self.cnx.commit()
        cursor.close()
