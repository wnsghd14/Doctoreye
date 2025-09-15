from django.contrib import messages
from django.shortcuts import redirect


def no_login_required(function):
    """
    로그인한 사용자가 접근하지 못하도록 방지하는 데코레이터
    """

    def wrapper(request, *args, **kwargs):
        # 로그인한 사용자인지 확인
        if request.user.is_authenticated:
            messages.warning(request, '이미 로그인한 상태입니다.')
            return redirect('main')

        # CSRF 토큰 오류가 발생한 경우, 데코레이터에서 처리하지 않고 미들웨어에 맡김
        if request.method == 'POST' and not request.META.get('CSRF_COOKIE'):
            return function(request, *args, **kwargs)

        return function(request, *args, **kwargs)

    return wrapper


def is_doctor_required(function):
    def wrapper(request, *args, **kwargs):
        user = request.user
        if hasattr(user, 'doctor'):
            return function(request, *args, **kwargs)
        else:
            print(f' user : { user}')
            messages.warning(request, '의사계정이 아닙니다.')
            return redirect('main')

    return wrapper



# todo : is_required 시 doctor_pk를 kwargs에서 가져온 이후, 확인절차를 거친다.
# todo : 이때에 내 request 와 doctor를 확인하고, 추후 고정 Personal IP테이블을 생성하여 해당 IP에서, 제대로 명시된 의사가 접속하는지 여부를 확인한다.
# todo : 아래 코드는 예시코드이며, 현재 사용이 가능한 함수가 여럿 있으나, 클라이언트들의 사용상 편리를 위해 우선 사용하지 않는다

# def is_doctor_authenticated(function):
#     def wrapper(request, *args, **kwargs):
#         user = request.user
#
#         doctor_pk = kwargs.get('doctor_pk')
#         # request.META.get('HTTP_AUTHORIZATION')
#         if doctor_pk == user.doctor.pk:
#             return function(request, *args, **kwargs)
#         else:
#             return redirect('main')
#
#     return wrapper
