from datetime import datetime
import re
from django.core.exceptions import ValidationError


def calculate_age(birthdate):
    # 현재 날짜를 얻음
    today = datetime.today()
    if type(birthdate) == str:
        birthdate = datetime.strptime(birthdate, '%Y-%m-%d')
    # 기본 나이 계산 (현재 연도에서 태어난 연도를 뺌)
    age = today.year - birthdate.year

    # 생일이 지났는지 여부를 확인하여 나이를 조정
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1

    return age


def validate_email_(value):
    pattern = r'^[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*(\.[a-zA-Z]{2,})+$'
    return bool(re.search(pattern, value))


def validate_password_(value):
    # 최소 8자, 특수문자 포함, 동일 숫자가 3번 이상 연속되면 안 됨
    if len(value) < 8 or not re.search(r'[!@#$%^&*(),.?":{}|<>]', value) or re.search(r'(\d)\1{2,}', value):
        return False
    return True


def mask_account(value):
    value = value[:50]
    mid = len(value) // 2
    return value[:mid] + "*" * (len(value) - mid)


def masked_reg_no(obj):
    if obj:
        reg_no = obj.patient_reg_no
        masked = f"{reg_no[:4]}{'*' * (len(reg_no) - 8)}{reg_no[-4:]}"
        return masked
    return "No reg_no"


def mask_email(value):
    local, domain = value.split('@')
    half_length = len(local) // 2
    masked_local = local[:half_length] + '*' * half_length
    return f"{masked_local}@{domain}"


def mask_korean_name(name):
    exception_list = ['남궁', '황보', '제갈', '사공', '서문', '선우', '독고', '동방']
    if len(name) > 1:

        for surname in exception_list:
            if name.startswith(surname):
                return surname + '*' * (len(name) - len(surname))
        return name[0] + '*' * (len(name) - 1)
    else:
        # 이름이 한 글자인 경우 그대로 반환합니다.
        return name


def get_hash_key():
    from django.conf import settings
    return f"{settings.FIELD_ENCRYPTION_KEYS}"


class Gender:
    GENDER_CHOICE = (
        ('0', '남'),
        ('1', '여')
    )

    @classmethod
    def get_gender_display(cls, value):
        gender_dict = dict(cls.GENDER_CHOICE)
        if value not in gender_dict:
            raise ValueError("Invalid value for gender. Only 0 or 1 is allowed.")
        return gender_dict[value]


class Disease:
    DISEASE_CHOICE = (
        ("AMD", "황반변성"),
        ("Diabetic", "당뇨망막병증"),
        ("ERM", "망막전막"),
        ("Glaucoma", "녹내장"),
        ("Normal", "정상")
    )

    @classmethod
    def get_disease_display(cls, value):
        """
        사용자 입력 value(리스트)를 정규화한 후,
        DISEASE_CHOICE에 정의된 각 항목도 동일하게 정규화하여
        해당하는 한글 라벨을 반환합니다.

        만약 일치하는 항목이 두 개 이상이면 리스트를, 하나이면 단일 값 반환.
        """
        # DISEASE_CHOICE에서 각 튜플의 첫 번째 요소(영문 이름)를 소문자로 변환하여 딕셔너리 생성
        normalized_dict = {
            key.lower(): label
            for key, label in dict(cls.DISEASE_CHOICE).items()
        }
        # normalized_dict의 키 목록
        normalized_keys = list(normalized_dict.keys())
        print(f'value: {value}')
        # 전달된 value는 리스트로 가정, 각 요소를 소문자로 정규화
        if type(value) != type(list()):
            normalized_values = [value]
        else:
            normalized_values = value
        # normalized_values의 각 요소가 normalized_keys에 존재하면 해당 라벨을 수집
        matches = [normalized_dict[val] for val in normalized_values if val in normalized_keys]
        print(f'matches: {matches}')
        if not matches:
            raise ValueError("Invalid value for disease.")

        # 결과가 하나면 단일 값, 여러 개면 리스트로 반환
        return matches[0] if len(matches) == 1 else matches

    @classmethod
    def get_disease_info(cls, user_input):
        """
        사용자 입력을 대소문자 구분 없이 정규화하여
        DISEASE_CHOICE에 있는 원본 튜플 (정식 표기, 한글 라벨)을 반환합니다.
        만약 매칭이 없으면 기본값 ("normal", "정상")을 반환합니다.

        user_input이 리스트라면, 그 리스트의 각 요소를 개별적으로 검사합니다.
        """
        # DISEASE_CHOICE의 각 튜플에서 첫 번째 요소(영문 이름)를 소문자로 추출
        disease_lit = [key.lower().strip() for key, label in cls.DISEASE_CHOICE]

        # user_input이 리스트이면 각 요소를 정규화, 아니면 하나의 값으로 처리
        if isinstance(user_input, list):
            normalized_values = [
                "diabetic" if val.lower().strip() == "diabetic retinopathy" else val.lower().strip()
                for val in user_input
            ]
        else:
            normalized_values = [user_input.lower().strip()]

        # 1. 정확한 매칭을 시도
        print(f'normalized_values: {normalized_values}')
        results = []
        # 정확한 매칭을 시도
        for normalized in normalized_values:
            if normalized in disease_lit:
                print(f'normalized_value: {normalized}')
                # 특별 처리가 필요한 경우 처리: 예를 들어, "diabetic retinopathy"는 "diabetic"로 처리
                results.append(normalized)
            else:
                # 부분 매칭 시도
                for key in disease_lit:
                    if normalized in key:
                        print(f'Partial match: {normalized} in {key}')
                        results.append(key)
                        break
        if not results:
            return "normal"
        # 결과가 하나면 단일 문자열, 여러 개면 리스트 반환
        print(f'Exact match found: {results}')
        return results[0] if len(results) == 1 else results