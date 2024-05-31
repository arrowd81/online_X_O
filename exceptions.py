class GameException(Exception):
    pass


class UserAlreadyExistsException(GameException):
    def __init__(self, user):
        super().__init__()
        self.user = user

    def __str__(self):
        return f'User {self.user} already exists'


class LobbyIsFullException(GameException):
    pass


class PositionIsFullException(GameException):
    pass
