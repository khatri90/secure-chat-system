from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
import jwt

User = get_user_model()

@database_sync_to_async
def get_user(validated_token):
    try:
        user_id = validated_token['user_id']
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Extract token from query string or headers
        token = None
        if "query_string" in scope:
            query_string = scope["query_string"].decode()
            query_params = dict(qp.split("=") for qp in query_string.split("&") if "=" in qp)
            token = query_params.get("token")

        if token:
            try:
                # Validate token
                UntypedToken(token)
                # Decode token to get user
                decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                scope["user"] = await get_user(decoded_data)
            except (InvalidToken, TokenError, jwt.DecodeError):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)

JwtAuthMiddlewareStack = lambda inner: JwtAuthMiddleware(inner)