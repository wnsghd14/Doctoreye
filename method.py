import random
import string
from typing import List, Tuple
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import date, datetime

from config.settings import APP_ENV
from doctors.models import PatientInfo
from datetime import datetime, timedelta
from django.db import models
from core.constants import VIEW_COUNT
from django.core.paginator import Paginator, EmptyPage


def get_test_doctor(test_account):
    """
    테스트용 의사 객체 가져오기
    """
    from doctors.models import Doctor
    from users.models import User
    user = User.available_objects.get(account=test_account)

    if hasattr(user, 'doctor'):
        doctor = Doctor.available_objects.get(user=user)
        print(f"기존 의사 '{doctor.doctor_info.name}'이(가) 가져와졌습니다.")
        return doctor
    else:
        return "error : 테스트용 의사 계정이 아닙니다. account 재입력하셈."


def create_get_patient_tmp(account=None):
    """
    테스트용 환자 객체를 생성하거나 가져오는 함수
    """
    from doctors.models import Patient
    from doctors.models import GENDER_CHOICE

    with transaction.atomic():
        patient = Patient.available_objects.create(doctor_id=get_test_doctor(account).id,
                                         patient_reg_no=generate_random_patient_reg_no())
        print(f"환자: {patient}")
        print(f"날짜 : {random_date('1960-01-01', '2000-01-01')}")
        print(f'typeof : {type(random_date("1960-01-01", "2000-01-01"))}')
        patient_name = generate_random_name()
        patient_info, patient_info_created = PatientInfo.available_objects.get_or_create(

            patient_id=patient.id, age=random_date('1960-01-01', '2000-01-01'), name=patient_name
            , gender=random.choice(["1", "0"])
        )
        print(f"새로운 환자 '{patient_name}'이(가) 생성되었습니다.")

    return patient


def create_of_patient_history_tmp(test_account, iteration=30):
    '''
    환자의 진료기록을 생성하는 함수
    '''
    from doctors.models import MedicalHistory
    from doctors.models import Patient

    doctor = get_test_doctor(test_account)
    patients_queryset = Patient.available_objects.filter(doctor_id=doctor.id)
    # 모든 테스트닥터에 종속된 환자 쿼리셋안의 객체에 대해 진료기록을 생성
    for patient in patients_queryset:
        with transaction.atomic():
            for i in range(iteration):
                MedicalHistory.available_objects.create(patient_id=patient.id)
                print(f"환자 '{patient.patient_info.name}'의 진료기록이 생성되었습니다.")


def create_get_user_tmp():
    """
    테스트용 사용자 객체를 생성하거나 가져오는 함수
    """
    User = get_user_model()
    username = generate_random_username()
    user, created = User.available_objects.get_or_create(
        account=username,
        defaults={
            'email': f"{username}@example.com"
        }
    )
    if created:
        print(f"새로운 사용자 '{username}'이(가) 생성되었습니다.")
    else:
        print(f"기존 사용자 '{username}'이(가) 가져와졌습니다.")
    return user


def generate_random_patient_reg_no():
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(12))
    return random_string


def generate_random_name():
    """
    랜덤한 한글 이름을 생성하는 함수
    """
    first_names = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임']
    middle_names = ['서', '준', '성', '민', '승', '영', '상']
    last_names = ['민', '준', '서', '현', '지', '수', '은', '아', '주', '영']
    return ''.join(random.choice(first_names) + random.choice(middle_names) + random.choice(last_names))


def generate_random_username():
    """
    랜덤한 영문 사용자명을 생성하는 함수
    """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(8))


def random_date(start_date: str, end_date: str) -> date:
    # Convert string dates to datetime available_objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Get a random number of days between start_date and end_date
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)

    # Generate the random date
    exact_date = start_date + timedelta(days=random_days)

    # Convert the datetime object back to string in YYYY-MM-DD format
    return exact_date.date()


def search_patients(patients: models.QuerySet, search: str) -> models.QuerySet:
    search_queryset = patients.filter(patient_info__name=search)
    return search_queryset


def paginate_queryset(queryset: models.QuerySet, request_page: int) -> Tuple:
    paginator = Paginator(queryset, VIEW_COUNT)
    try:
        page = paginator.page(request_page)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    page_index_lst = get_page_data_index(paginator, request_page)
    return page.object_list, paginator.num_pages, page_index_lst


def get_page_data_index(paginator: Paginator, page_number: int) -> List:
    # page = 2일 경우 21부터 40 index list 반환
    start_index = (page_number - 1) * VIEW_COUNT + 1
    end_index = start_index + VIEW_COUNT - 1
    return list(range(start_index, end_index + 1))


def get_adjacent_pages(current_page: int, last_page: int, num_adjacent: int) -> List:
    start_page = max(current_page - num_adjacent, 1)
    end_page = min(current_page + num_adjacent, last_page)

    if start_page > 1:
        start_page -= 1

    if end_page < last_page:
        end_page += 1

    return list(range(start_page, end_page + 1))


def filter_queryset_by_date(date_string, histories: models.QuerySet) -> models.QuerySet:
    date_obj = datetime.strptime(date_string, "%Y-%m-%d").date()
    year = date_obj.year
    month = date_obj.month
    histories = histories.filter(created__year=year, created__month=month)
    return histories
