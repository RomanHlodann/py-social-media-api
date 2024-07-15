from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_extra import NinjaExtraAPI, api_controller, route
from django.contrib.auth import get_user_model

from users.schemas import UserCreationSchema, RegisterResponseSchema, Error


api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)
User = get_user_model()


@api_controller()
class RegisterController:
    @route.post(
        "/register",
        response={200: RegisterResponseSchema, 400: Error}
    )
    def register(self, request, user: UserCreationSchema):
        if User.objects.filter(username=user.username).exists():
            return 404, {"message": "Username already exists"}

        user = User.objects.create_user(
            username=user.username,
            password=user.password,
            email=user.email
        )
        return {"id": user.id, "username": user.username}


api.register_controllers(RegisterController)
