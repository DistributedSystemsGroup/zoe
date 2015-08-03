import mysql.connector

db = None


class CAaaSSQL:
    def __init__(self):
        self.cnx = None

    def connect(self, user, passw, server, dbname):
        assert self.cnx is None
        self.cnx = mysql.connector.connect(user=user, password=passw, host=server, database=dbname)

    def _check_user(self, username):
        cursor = self.cnx.cursor(dictionary=True)
        q = "SELECT id FROM users WHERE username=%s"

        cursor.execute(q, (username,))
        if cursor.rowcount == 0:
            cursor.close()
            return self._create_user(username)
        else:
            row = cursor.fetchone()
            cursor.close()
            return row["id"]

    def _create_user(self, username):
        cursor = self.cnx.cursor()
        q = "INSERT INTO users (username) VALUES (%s)"
        cursor.execute(q, username)
        user_id = cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return user_id


def init_db(user, passw, server, dbname):
    global db
    db = CAaaSSQL()
    db.connect(user, passw, server, dbname)
