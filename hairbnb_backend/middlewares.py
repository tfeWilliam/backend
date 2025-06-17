from django.http import HttpResponseForbidden

class BlockWordPressScannersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        blocked_keywords = [
            'wp-includes', 'wp-admin', 'xmlrpc.php', 'wlwmanifest.xml', 'wp-content'
        ]
        if any(keyword in request.path for keyword in blocked_keywords):
            return HttpResponseForbidden("Access Denied")
        return self.get_response(request)
