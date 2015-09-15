class ZoeException(Exception):
    def __init__(self):
        self.value = 'Something happened'

    def __str__(self):
        return repr(self.value)


class CannotCreateCluster(ZoeException):
    def __init__(self, application):
        self.value = "Cannot create a cluster for application {}".format(application.id)
