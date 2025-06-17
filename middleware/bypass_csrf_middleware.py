from django.utils.deprecation import MiddlewareMixin


class BypassCSRFMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            setattr(request, "_dont_enforce_csrf_checks", True)
