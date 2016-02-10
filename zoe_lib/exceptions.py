class ZoeException(Exception):
    def __init__(self, value='Something happened'):
        self.value = value

    def __str__(self):
        return self.value


class ZoeAPIException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class InvalidApplicationDescription(ZoeAPIException):
    def __init__(self, msg):
        self.message = msg


class ZoeRestAPIException(ZoeException):
    def __init__(self, message, status_code=400, headers=None):
        super().__init__(value=message)
        self.status_code = status_code
        self.headers = headers
