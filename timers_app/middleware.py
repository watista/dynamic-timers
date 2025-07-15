import logging

access_logger = logging.getLogger("access")

class AccessLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        ip = get_client_ip(request)
        method = request.method
        path = request.get_full_path()
        status = response.status_code
        user_agent = request.META.get("HTTP_USER_AGENT", "-")

        access_logger.info(f'{ip} - "{method} {path}" {status} "{user_agent}"')
        return response

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
