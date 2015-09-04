class ZoeException(Exception):
    def __init__(self):
        self.value = 'Something happened'

    def __str__(self):
        return repr(self.value)


class UserIDDoesNotExist(ZoeException):
    def __init__(self, user_id):
        self.value = "The user ID {} does not exist".format(user_id)


class ApplicationStillRunning(ZoeException):
    def __init__(self, application):
        self.value = "The application {} cannot be removed because it is in use".format(application.id)


class CannotCreateCluster(ZoeException):
    def __init__(self, application):
        self.value = "Cannot create a cluster for application {}".format(application.id)
