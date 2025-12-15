import secrets

from django.utils.deprecation import MiddlewareMixin


class ClientTokenMiddleware(MiddlewareMixin):
    """
    Issues a client_token cookie for anonymous users to associate temporary edit rights.
    """

    COOKIE_NAME = "client_token"

    def process_request(self, request):
        token = request.COOKIES.get(self.COOKIE_NAME)
        if not token:
            # 128-bit token base16; kept simple. Could use base62 if needed.
            request._new_client_token = secrets.token_hex(16)

    def process_response(self, request, response):
        new_token = getattr(request, "_new_client_token", None)
        if new_token:
            # Session length cookie
            response.set_cookie(self.COOKIE_NAME, new_token, max_age=30 * 60, httponly=True, samesite="Lax")
        return response
