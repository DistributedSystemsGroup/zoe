class User:
    def __init__(self, user: dict):
        self.id = user['id']
        self.email = user['email']
