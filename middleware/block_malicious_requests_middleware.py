# middleware/block_malicious_requests.py
from django.http import HttpResponseBadRequest

class BlockMaliciousRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.blocked_paths = [
            '/sslvpnLogin.html',
            '/api/sonicos/auth',
            '/api/sonicos/tfa',
            '/auth.html',
            '/auth1.html'
            '/wsman'
        ]

    def __call__(self, request):
        if request.path in self.blocked_paths:
            return HttpResponseBadRequest("Bad request.")
        return self.get_response(request)
