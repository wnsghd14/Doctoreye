# django
import uuid
from io import BytesIO
from time import sleep
import datetime

import requests
from django.contrib import messages

# core
from core import constants

from core.utils import Disease, Gender, calculate_age
# apps
from doctors.helpers import QueryStringHelper

from doctors.models import (DiagnosisFile, DiseaseLeft, DiseaseRight, FundusHitmapImageLeft, FundusHitmapImageRight,
                            FundusImageLeft, Doctor,
                            FundusImageRight, MedicalHistory, MemoHistory, Patient, PatientInfo)

from django.db import models
from typing import List, Optional, Dict
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from django.db.models.fields.files import ImageFieldFile

from django.conf import settings
import base64


def create_one_hot_encoding(name_tags):
    """
    진단 결과 페이지 템플릿용 함수
    입력: name_tags - abnormal 조건이 포함된 리스트.
         예: ['당뇨망막병증', '녹내장']
    출력: 각 조건에 따라 one-hot 인코딩 리스트 반환.
         기본은 모두 '정상'이며, 해당 조건에 대해 '비정상'으로 표시합니다.

    조건 인덱스 매핑:
      - '황반변성' 또는 'amd'            -> index 0
      - '당뇨망막병증' 또는 'diabetic'    -> index 1
      - '녹내장' 또는 'glaucoma'          -> index 2
      - '망막전막' 또는 'erm'             -> index 3

    만약 입력이 단일 문자열이면 리스트로 변환하여 처리합니다.
    """
    # 입력이 리스트가 아니면 리스트로 변환
    if not isinstance(name_tags, list):
        name_tags = [name_tags]
    print(f'name_tags: {name_tags}')
    # 기본 인코딩: 모든 값이 '정상'
    encoding = ['정상', '정상', '정상', '정상']

    # 조건 매핑: 영어와 한글 모두를 처리할 수 있도록 설정
    condition_mapping = {
        'diabetic': 0, '당뇨망막병증': 0,
        'amd': 1, '황반변성': 1,
        'glaucoma': 2, '녹내장': 2,
        'erm': 3, '망막전막': 3,
    }

    # 입력된 각 조건에 대해 매핑이 있다면 해당 인덱스를 '비정상'으로 설정
    for tag in name_tags:
        normalized_tag = tag.lower().strip()
        if normalized_tag in condition_mapping:
            encoding[condition_mapping[normalized_tag]] = '비정상'
        else:
            print(f"Warning: '{normalized_tag}' is not recognized in condition_mapping.")

    return encoding


def encode_image_to_base64(image_file):
    """
    주어진 InMemoryUploadedFile 또는 UploadedFile 객체를 base64로 인코딩합니다.
    """

    image_file.seek(0)
    img_base64 = base64.b64encode(image_file.read()).decode()
    return img_base64


def load_img_base(path):
    with open(path, "rb") as img_file:
        bytes = img_file.read()
    img_base64 = base64.b64encode(bytes).decode()
    return img_base64


def get_object_or_none(model, **kwargs):
    smtm = model.objects.filter(**kwargs)
    if smtm.exists():
        return smtm.first()
    return None


class MedicalRecodeInfo:
    def __init__(self, patient_pk, history_pk):
        self.patient_pk = patient_pk
        self.history_pk = history_pk

        self.name = None
        self.age = None
        self.sex = None
        self.date = None
        self.time = None
        self.left_img_path = None
        self.left_label = None
        self.left_data_value = None
        self.right_img_path = None
        self.right_label = None
        self.right_data_value = None
        self.logo_img_path = load_img_base('static/images/logo/logo.png')
        self.hit_left_path = None
        self.hit_right_path = None
        self.patient_reg_no = None

        self.obj = {
            "patient_info": None,
            "medical_history": None,
            "memo_history": None,
            "fundus_image_left": None,
            "fundus_image_right": None,
            "disease_left": None,
            "disease_right": None,
            "fundus_hit_left": None,
            "fundus_hit_right": None,
        }

    def get_basic_info(self):
        return {
            "name": self.name,
            "age": self.age,
            "sex": self.sex,
            "date": self.date,
            "time": self.time,
            "left_img_path": self.left_img_path,
            "left_label": self.left_label,
            "left_data_value": self.left_data_value,
            "right_img_path": self.right_img_path,
            "right_label": self.right_label,
            "right_data_value": self.right_data_value,
            "logo_img_path": self.logo_img_path,
            "hit_left_path": self.hit_left_path,
            "hit_right_path": self.hit_right_path,
            "patient_reg_no": self.patient_reg_no,
        }

    def processor_diagnose_result_data_maker(self):
        self.build_name()
        self.build_age()
        self.build_sex()
        self.build_date_time()
        self.build_fundus_image_left()
        self.build_fundus_image_right()
        self.build_disease_left()
        self.build_disease_right()
        self.build_hit_left()
        self.build_hit_right()
        self.build_patient_reg_no()

    def build_patient_reg_no(self):
        # patient_reg_no가 이미 채워져 있다면 그대로 반환
        if not hasattr(self, 'patient_reg_no') or self.patient_reg_no is None:
            # self.patient_pk로 Patient 객체를 조회 (get_object_or_none는 None 반환 가능)
            patient: Optional[Patient] = get_object_or_none(Patient, pk=self.patient_pk)
            if patient:
                self.patient_reg_no = patient.patient_reg_no
            else:
                self.patient_reg_no = None
        return self.patient_reg_no

    def get_dict_info(self):
        return self.__dict__

    def get_patient_info(self):
        if self.obj['patient_info'] == None:
            patient_info: Optional[PatientInfo] = get_object_or_none(PatientInfo, patient_id=self.patient_pk)
            self.obj['patient_info'] = patient_info
        return self.obj.get('patient_info')

    def get_medical_history(self):
        if self.obj['medical_history'] == None:
            medical_history: Optional[MedicalHistory] = get_object_or_none(MedicalHistory, id=self.history_pk)
            self.obj['medical_history'] = medical_history
        return self.obj.get('medical_history')

    def get_fundus_image_left(self):
        if self.obj['fundus_image_left'] == None:
            fundus_image_left: Optional[FundusImageLeft] = get_object_or_none(FundusImageLeft,
                                                                              medical_history_id=self.history_pk)
            self.obj['fundus_image_left'] = fundus_image_left
        return self.obj.get('fundus_image_left')

    def get_fundus_image_right(self):
        if self.obj['fundus_image_right'] == None:
            fundus_image_right: Optional[FundusImageRight] = get_object_or_none(FundusImageRight,
                                                                                medical_history_id=self.history_pk)
            self.obj['fundus_image_right'] = fundus_image_right
        return self.obj.get('fundus_image_right')

    def get_disease_left(self):
        if self.obj['disease_left'] == None:
            if self.obj['fundus_image_left'] != None:
                disease_left: Optional[DiseaseLeft] = get_object_or_none(DiseaseLeft, fundus_left_id=self.obj.get(
                    'fundus_image_left').id)
                self.obj['disease_left'] = disease_left
                print(f'disease_left : {disease_left}')
        return self.obj.get('disease_left')

    def get_disease_right(self):
        if self.obj['disease_right'] == None:
            if self.obj['fundus_image_right'] is not None and isinstance(self.obj['fundus_image_right'], FundusImageRight):
                disease_right: Optional[DiseaseRight] = get_object_or_none(DiseaseRight, fundus_right_id=self.obj.get(
                    'fundus_image_right').id)
                self.obj['disease_right'] = disease_right
                print(f'disease_right : {disease_right}')
        return self.obj.get('disease_right')

    def get_hit_left(self):
        if self.obj['fundus_hit_left'] == None:
            if self.obj['fundus_image_left'] != None and isinstance(self.obj['fundus_image_left'], FundusImageLeft):
                fundus_hit_left: Optional[FundusHitmapImageLeft] = get_object_or_none(FundusHitmapImageLeft,
                                                                                      fundus_left_id=self.obj.get(
                                                                                          'fundus_image_left').id)
                self.obj['fundus_hit_left'] = fundus_hit_left
        return self.obj.get('fundus_hit_left')

    def get_hit_right(self):
        if self.obj['fundus_hit_right'] == None:
            if self.obj['fundus_image_right'] != None and isinstance(self.obj['fundus_image_right'], FundusImageRight):
                fundus_hit_right: Optional[FundusHitmapImageRight] = get_object_or_none(FundusHitmapImageRight,
                                                                                        fundus_right_id=self.obj.get(
                                                                                            'fundus_image_right').id)
                self.obj['fundus_hit_right'] = fundus_hit_right
        return self.obj.get('fundus_hit_right')


    def build_name(self):
        patient_info = self.get_patient_info()
        if isinstance(patient_info, PatientInfo):
            if hasattr(patient_info, 'name'):
                if isinstance(patient_info.name, str):
                    self.name = patient_info.name
                # 옝except handeler

    def build_age(self):
        patient_info = self.get_patient_info()
        if isinstance(patient_info, PatientInfo):
            if hasattr(patient_info, 'age'):
                if isinstance(patient_info.age, datetime.date):
                    self.age = calculate_age(patient_info.age)

    def build_sex(self):
        patient_info = self.get_patient_info()
        if isinstance(patient_info, PatientInfo):
            if hasattr(patient_info, 'gender'):
                if isinstance(patient_info.gender, str):
                    self.sex = Gender.get_gender_display(patient_info.gender)

    def build_date_time(self):
        medical_history = self.get_medical_history()
        if isinstance(medical_history, MedicalHistory):
            if hasattr(medical_history, 'created'):
                if isinstance(medical_history.created, datetime.datetime):
                    self.date = medical_history.created.date()
                    self.time = medical_history.created.time()

    def build_fundus_image_left(self):
        fundus_image_left = self.get_fundus_image_left()
        if isinstance(fundus_image_left, FundusImageLeft):
            if hasattr(fundus_image_left, 'left_image'):
                if isinstance(fundus_image_left.left_image, ImageFieldFile):
                    self.left_img_path = encode_image_to_base64(fundus_image_left.left_image)

    def build_fundus_image_right(self):
        fundus_image_right = self.get_fundus_image_right()
        if isinstance(fundus_image_right, FundusImageRight):
            if hasattr(fundus_image_right, 'right_image'):
                if isinstance(fundus_image_right.right_image, ImageFieldFile):
                    self.right_img_path = encode_image_to_base64(fundus_image_right.right_image)

    def build_disease_left(self):
        disease_left = self.get_disease_left()
        print(f'disease_left : {disease_left.get_field_with_value_1()}')
        if disease_left:
            self.left_label = Disease.get_disease_display(disease_left.get_field_with_value_1())
            self.left_data_value = create_one_hot_encoding(disease_left.get_field_with_value_1())

    def build_disease_right(self):
        disease_right = self.get_disease_right()
        if disease_right:
            self.right_label = Disease.get_disease_display(disease_right.get_field_with_value_1())
            self.right_data_value = create_one_hot_encoding(disease_right.get_field_with_value_1())

    def build_hit_left(self):
        fundus_hit_left = self.get_hit_left()
        if isinstance(fundus_hit_left, FundusHitmapImageLeft):
            if hasattr(fundus_hit_left, 'hit_image_left'):
                if isinstance(fundus_hit_left.hit_image_left, ImageFieldFile):
                    self.hit_left_path = encode_image_to_base64(fundus_hit_left.hit_image_left)

    def build_hit_right(self):
        fundus_hit_right = self.get_hit_right()
        if isinstance(fundus_hit_right, FundusHitmapImageRight):
            if hasattr(fundus_hit_right, 'hit_image_right'):
                if isinstance(fundus_hit_right.hit_image_right, ImageFieldFile):
                    self.hit_right_path = encode_image_to_base64(fundus_hit_right.hit_image_right)


def get_patients_history_result(patient_pk: str, history_pk: str) -> Dict:
    infoMaker = MedicalRecodeInfo(patient_pk=patient_pk, history_pk=history_pk)
    infoMaker.processor_diagnose_result_data_maker()
    return infoMaker.get_basic_info()


def get_patients(req_meta_qs: str, doctor_pk: str) -> Dict:
    try:
        patients: models.QuerySet[Patient] = Patient.objects.filter(doctor_id=doctor_pk)
        qs_helper = QueryStringHelper(query_string=req_meta_qs, pk_set={'doctor_pk': doctor_pk})
        query_set = qs_helper.search_controller(patients)
        query_set = qs_helper.page_controller(query_set)
        num_page, page_index, adjacent_pages = qs_helper.num_page, qs_helper.page_index, qs_helper.adjacent_pages
        patients_data: list = get_patients_data(query_set, page_index)
        doctors_data: dict = get_doctor_data(Doctor.objects.filter(id=doctor_pk).first())
        pages_data: list = get_page_data(adjacent_pages)
        return {
            'patients': patients_data,
            'doctor': doctors_data,
            'pages': pages_data,
            'current_page': qs_helper.get_int("page"),
            'search_name': qs_helper.get('search')
        }
    except:
        return dict()


def base64_to_bytes(base64_str):
    import base64
    return base64.b64decode(base64_str)


def convert_to_inmemory_uploaded_file(io_bytes):
    return InMemoryUploadedFile(
        io_bytes,
        field_name=None,
        name=f'{uuid.uuid4()}.jpg',
        content_type='image/jpeg',
        size=io_bytes.getbuffer().nbytes,
        charset=None
    )


def save_diagnosis_info(request, doctor_pk):
    post = request.POST
    eye_images = request.FILES.getlist('eye_image_input')
    reg_no = f'{post.get("reg_no")}_{request.user.account}'
    files_for_request = {}

    # 각 이미지의 이름을 UUID 기반으로 재설정 후, FormData에 추가
    for idx, image in enumerate(eye_images):
        image.name = f'{uuid.uuid4()}.jpg'
        files_for_request[f"file{idx + 1}"] = (image.name, image.file.getvalue(), image.content_type)

    classify_url = settings.CLASSIFY_URL
    upload_url = settings.UPLOAD_URL

    # Classification API 호출
    try:
        classify_response = requests.post(classify_url, files=files_for_request)
        classify_response.raise_for_status()
        data = classify_response.json()
    except requests.RequestException as e:
        print(f"Classification API 오류: {e}")
        messages.warning(request, "❌ 이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요.")
        sleep(2)
        return {"status": "error", "message": "이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요."}

    # 왼쪽과 오른쪽 눈 이미지 구분
    left_eye, right_eye = None, None
    for image in eye_images:
        if image.name == data.get("left_eye"):
            left_eye = image
        else:
            right_eye = image

    files_for_request_2 = {"left_eye": left_eye, "right_eye": right_eye}
    # Upload API 호출
    try:
        upload_response = requests.post(upload_url, files=files_for_request_2)
        upload_response.raise_for_status()
        data = upload_response.json()
    except requests.RequestException as e:
        print(f"Upload API 오류: {e}")
        messages.warning(request, "❌ 이미지 업로드 중 오류가 발생했습니다. 다시 시도해주세요.")
        sleep(2)
        return {"status": "error", "message": "이미지 업로드 중 오류가 발생했습니다. 다시 시도해주세요."}

    # 질병 정보 정규화 (Disease.get_disease_info는 dict 대신 튜플 (정식 표기, 한글 라벨)을 반환)
    print(f'data : {data.get("left_eye_prediction")} | data : {data.get("right_eye_prediction")}')
    left_eye_prediction = Disease.get_disease_info(data.get("left_eye_prediction"))
    right_eye_prediction = Disease.get_disease_info(data.get("right_eye_prediction"))
    print(f'left_eye_prediction : {left_eye_prediction}')
    print(f'right_eye_prediction : {right_eye_prediction}')
    # hitmap 이미지 복원
    hit_map_left_bytes = base64_to_bytes(data.get('hit_map_left'))
    hit_map_right_bytes = base64_to_bytes(data.get('hit_map_right'))
    hit_map_left_image = convert_to_inmemory_uploaded_file(BytesIO(hit_map_left_bytes))
    hit_map_right_image = convert_to_inmemory_uploaded_file(BytesIO(hit_map_right_bytes))

    try:
        from django.db import transaction
        with transaction.atomic():

            patient = Patient.get_or_create_patient(doctor_id=doctor_pk, reg_no=reg_no)
            patient_info = PatientInfo.get_or_create_patient_info(
                patient.id, post.get('name'), post.get('birth'), post.get('sex')
            )
            medical_history = MedicalHistory.objects.create(patient_id=patient.id)
            memo_history = MemoHistory.get_or_create_memo_history(
                medical_history.id, post.get('symptom_by_patient'), post.get('memo_by_doctor')
            )
            fundus_image_left = FundusImageLeft.get_or_create_fil(medical_history.id, left_eye)
            fundus_image_right = FundusImageRight.get_or_create_fir(medical_history.id, right_eye)
            disease_left, _ = DiseaseLeft.get_or_create_with_condition(
                fundus_left_id=fundus_image_left.id, disease_type=left_eye_prediction
            )
            disease_right, _ = DiseaseRight.get_or_create_with_condition(
                fundus_right_id=fundus_image_right.id, disease_type=right_eye_prediction
            )
            diagnose_file = DiagnosisFile.get_or_create_file(medical_history.id)
            fundus_hit_left = FundusHitmapImageLeft.get_or_create_hit_left(
                fundus_image_left.id, hit_map_left_image
            )
            fundus_hit_right = FundusHitmapImageRight.get_or_create_hit_right(
                fundus_image_right.id, hit_map_right_image
            )
    except Exception as e:
        print(f"DB 저장 중 오류 발생: {e}")
        messages.warning(request, "❌ 데이터 저장 중 오류가 발생했습니다. 다시 시도해주세요.")
        sleep(2)
        return {"status": "error", "message": "데이터 저장 중 오류가 발생했습니다. 다시 시도해주세요."}

    # 여러 인스턴스를 저장
    instances_to_save = [
        patient, patient_info, medical_history, memo_history, fundus_image_left,
        fundus_image_right, disease_left, disease_right, diagnose_file,
        fundus_hit_left, fundus_hit_right
    ]

    for instance in instances_to_save:
        try:
            instance.save()
        except Exception as e:
            print(f"{instance} 저장 실패: {e}")
            messages.warning(request, "❌ 일부 데이터 저장 중 오류가 발생했습니다.")
            sleep(2)
            return {"status": "error", "message": "일부 데이터 저장 중 오류가 발생했습니다."}

    history_pk = getattr(medical_history, 'id', None) or None
    patient_pk = getattr(patient, 'id', None) or None

    info_maker = MedicalRecodeInfo(patient_pk=patient_pk, history_pk=history_pk)
    info_maker.processor_diagnose_result_data_maker()
    return info_maker.get_basic_info()


def get_patients_detail(req_meta_qs, patient_pk):
    try:
        qs_helper = QueryStringHelper(query_string=req_meta_qs, pk_set={'patient_pk': patient_pk})
        query_set = qs_helper.search_controller(query_set=MedicalHistory.objects.filter(patient_id=patient_pk))
        query_set = qs_helper.page_controller(query_set)

        num_page, page_index, adjacent_pages = qs_helper.num_page, qs_helper.page_index, qs_helper.adjacent_pages

        patient_history_data = [
            {
                'created': history.created,
                'patient_id': patient_pk,
                'history_id': history.id,
            }
            for history, index in zip(query_set, page_index)
        ]

        pages_data = [
            {
                'num_page': page,
            } for page in adjacent_pages
        ]
        return {
            'patient': get_object_or_none(Patient, id=patient_pk),
            'patient_history': patient_history_data,
            'pages': pages_data,
            'current_page': qs_helper.get_int('page')
        }
    except:
        return dict()


def get_patient_info(patient: Patient) -> Dict:
    """
    환자 정보를 가져옵니다.
    """
    try:
        patient_info = patient.patient_info
        medical_history = patient.medical_history.first()

        return {
            'name': patient_info.name if patient_info else "NoName",
            'gender': Gender.get_gender_display(patient_info.gender) if patient_info else "NoGender",
            'age': patient_info.age if patient_info else "NoAge",
            'recent': medical_history.created if medical_history else "No history"
        }
    except:
        return {
            'name': 'NoName',
            'gender': "NoGender",
            'age': "NoAge",
            'recent': "No history"
        }


def get_doctor_data(doctor: Doctor) -> Dict:
    """
    의사 정보를 가져옵니다.
    """
    doctor_info = doctor.doctor_info
    return {
        'name': doctor_info.name if doctor_info else "ErrorDoctorName",
        'user_id': doctor.user_id
    }


def get_page_data(adjacent_pages: List[int]) -> List[Dict]:
    """
    페이지 데이터를 가져옵니다.
    """
    return [{'num_page': page} for page in adjacent_pages]


def get_patients_data(patients: List[Patient], page_index: List[int]) -> List[Dict]:
    """
    환자 데이터를 가져옵니다.
    """
    return [
        {
            **get_patient_info(patient),
            'patient_id': patient.id
        }
        for patient, index in zip(patients, page_index)
    ]
