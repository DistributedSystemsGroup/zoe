class CAaaSException(Exception):
    def __init__(self):
        self.value = 'Something happened'

    def __str__(self):
        return repr(self.value)

class UserIDDoesNotExist(Exception):
    def __init__(self, user_id):
        self.value = "The user ID {} does not exist".format(user_id)
