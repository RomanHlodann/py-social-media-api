from ninja import Schema


class UserCreationSchema(Schema):
    username: str
    password: str
    email: str = None


class RegisterResponseSchema(Schema):
    id: int
    username: str


class Error(Schema):
    message: str
