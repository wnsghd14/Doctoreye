from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def signup_or_login(request):
    if request.path == '/users/prepare_signup/':
        return mark_safe('<a href="/users/prepare_forgot_account/" class="text-secondary-14">아이디찾기</a> | <a href="/users/prepare_forgot_password/" class="text-secondary-14">비밀번호찾기</a> | <a class="text-secondary-14" href="/users/prepare_login/">로그인</a>')
    elif request.path == '/users/prepare_login/':
        return mark_safe(
            '<a href="/users/prepare_forgot_account/" class="text-secondary-14">아이디찾기</a> | <a href="/users/prepare_forgot_password/" class="text-secondary-14">비밀번호찾기</a> | <a class="text-secondary-14" href="/users/prepare_signup/">회원가입</a>')
    elif request.path == '/users/prepare_forgot_password/':
        return mark_safe('<a href="/users/prepare_forgot_account/" class="text-secondary-14">아이디찾기</a> | <a class="text-secondary-14" href="/users/prepare_login/">로그인</a> | <a class="text-secondary-14" href="/users/prepare_signup/">회원가입</a>')
    elif request.path == '/users/prepare_forgot_account/':
        return mark_safe('<a href="/users/prepare_forgot_password/" class="text-secondary-14">비밀번호찾기</a> | <a class="text-secondary-14" href="/users/prepare_login/">로그인</a> | <a class="text-secondary-14" href="/users/prepare_signup/">회원가입</a>')

@register.filter
def to(value, arg):
    return range(value, arg + 1)


@register.filter
def mod_result(value):
    if value == "정상":
        return "-"
    return "O"

@register.filter
def is_list(value):
    return isinstance(value, list)

@register.filter
def contains(value, arg):
    """
    value가 리스트면 arg가 그 리스트에 포함되어 있는지 확인.
    아니라면 value와 arg를 직접 비교합니다.
    """
    if isinstance(value, list):
        return arg in value
    return value == arg

from datetime import timedelta
from django.utils.timezone import is_naive, make_aware, get_current_timezone

@register.filter
def minus_1year(value):
    if not value:
        return None
    if is_naive(value):
        value = make_aware(value, get_current_timezone())
    return value - timedelta(days=365)