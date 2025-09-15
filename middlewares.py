from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from core.models import AllowedIP
from users.forms import LoginForm


# For healthcheck(server)
class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health':
            return HttpResponse('ok')
        return self.get_response(request)


class RequestLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.prefixs = ['/admin', ]

    def __call__(self, request):
        import time
        _t = time.time()  # Calculated execution time.
        response = self.get_response(request)  # Get response from view function.
        _t = int((time.time() - _t) * 1000)

        # todo : If prefix needed how describing this
        if any(request.path.startswith(prefix) for prefix in self.prefixs) or \
                request.path.startswith('/static/') or request.path.endswith('.ico'):
            return self.get_response(request)
        # Create instance of our model and assign values
        from core.models import RequestLogger
        req_b = ''
        try:
            req_b = request.body.decode()
            if req_b == '':
                req_body = req_b
            else:
                from urllib.parse import parse_qs
                req_body = parse_qs(req_b)

        except Exception as e:
            print(f'e : {e}')
            req_body = str(f'e : {e}, raw : {req_b}')
        try:
            res_body = response.content.decode()
        except Exception as e:
            print(f'response exception : {e}')
            res_body = e
        session_key = request.session.session_key
        request_log = RequestLogger(
            endpoint=request.get_full_path(),
            response_code=response.status_code,
            method=request.method,
            remote_address=self.get_client_ip(request),
            exec_time=_t,
            body_response=res_body,
            body_request=req_body,
            session_key=session_key
        )
        try:
            # Assign user to log if it's not an anonymous user
            if request.user.is_authenticated:
                request_log.user = request.user
        except Exception as e:
            print(f'user type exception : {e}')

        # Save log in db
        request_log.save()
        return response

    # get clients ip address
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            _ip = x_forwarded_for.split(',')[0]
        else:
            _ip = request.META.get('REMOTE_ADDR')
        return _ip


class RedirectAllErrorsMiddleware(MiddlewareMixin):
    """
    400~599 모든 오류 발생 시 자동으로 'main' 페이지로 리디렉트하는 미들웨어
    오류 메시지는 Django messages에 추가
    단, DEBUG=True일 때는 미들웨어가 동작하지 않도록 예외 처리
    """

    def process_response(self, request, response):
        # DEBUG=True일 때는 미들웨어 비활성화
        from django.conf import settings
        if settings.DEBUG:
            return response

        # API 요청("/api/")은 예외 처리
        if request.path.startswith("/api/"):
            return response

        # 400~599 에러 발생 시 리디렉트
        if 400 <= response.status_code < 600:
            error_message = f"❌ 오류 발생: {response.status_code} - {response.reason_phrase}"
            print(f"[ERROR] {request.path} - {response.status_code}: {response.reason_phrase}")
            return redirect(f"{reverse('main')}?error=알 수 없는 오류입니다. 다시 시도하거나, 담당자에게 문의하세요.")

        return response


class IPWhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        client_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        allowed_ips = AllowedIP.objects.values_list('ip_address', flat=True)
        print(f'client_ip : {client_ip}')
        if client_ip not in allowed_ips:
            request.session.flush()  # 세션 강제 종료
            path = request.path
            form = LoginForm()
            if path == "/" or path == "/users/prepare_login/":
                messages.warning(request, "🚫 접속이 허용되지 않은 IP입니다. 관리자에게 문의하여 주세요.")
            else:
                messages.warning(request, "🚫 접속이 허용되지 않은 IP입니다. 웹사이트를 사용하려면, 관리자에게 문의하여 주세요.")
            return render(request, 'users/sign.html', {
                'form': form,
                'url': '/users/login/',
            })
        return self.get_response(request)