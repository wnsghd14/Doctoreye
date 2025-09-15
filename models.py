from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from encrypted_fields.fields import EncryptedCharField, SearchField, EncryptedDateField
from model_utils.models import SoftDeletableModel, TimeStampedModel, UUIDModel
from core.constants import CLASS_NAME_DISEASES, DANGER_LEVEL, GENDER_CHOICE
from core.utils import mask_korean_name, Disease


class Doctor(SoftDeletableModel, TimeStampedModel, UUIDModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='doctor')

    class Meta:
        ordering = ['-created']
        verbose_name = '의사 정보'
        verbose_name_plural = '의사 정보'

    def __str__(self):
        return f"{mask_korean_name(self.doctor_info.name)}"


class DoctorInfo(SoftDeletableModel, TimeStampedModel, UUIDModel):
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name='doctor_info')
    _name = EncryptedCharField(max_length=100)
    name = SearchField(hash_key=settings.ENC_FIELD_KEY, encrypted_field_name="_name")

    class Meta:
        ordering = ['-created']


class Patient(SoftDeletableModel, TimeStampedModel, UUIDModel):
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='patients')
    patient_reg_no = models.CharField(max_length=100, unique=True, null=False, blank=False)

    class Meta:
        ordering = ['-created']
        verbose_name = '환자 정보'
        verbose_name_plural = '환자 정보'

    def __str__(self):
        return f"{mask_korean_name(self.patient_info.name)}"

    @classmethod
    def get_or_create_patient(cls, reg_no, doctor_id):
        patient, _ = cls.available_objects.get_or_create(patient_reg_no=reg_no, doctor_id=doctor_id,
                                                         defaults={'doctor_id': doctor_id,
                                                                   'patient_reg_no': reg_no})
        return patient


class PatientInfo(SoftDeletableModel, TimeStampedModel, UUIDModel):
    _name = EncryptedCharField(max_length=100)
    name = SearchField(hash_key=settings.ENC_FIELD_KEY, encrypted_field_name="_name")
    gender = models.CharField(choices=GENDER_CHOICE, max_length=1)
    _age = EncryptedDateField()
    age = SearchField(hash_key=settings.ENC_FIELD_KEY, encrypted_field_name="_age")
    # 추가 필요: 형식논의 필요: null=True, blank=True 임시로 해놓음!
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='patient_info')

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{mask_korean_name(self.name)}"

    @classmethod
    def get_or_create_patient_info(cls, patient_id, name, age, gender):
        patient_info, _ = cls.available_objects.get_or_create(patient_id=patient_id,
                                                              defaults={'patient_id': patient_id,
                                                                        'name': name,
                                                                        'age': age,
                                                                        'gender': gender
                                                                        })
        return patient_info


class MedicalHistory(SoftDeletableModel, TimeStampedModel, UUIDModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')

    class Meta:
        ordering = ['-created']
        verbose_name = '환자 방문 히스토리'
        verbose_name_plural = '환자 방문 히스토리'

    def __str__(self):
        return f"medical_history_patient"


class DiagnosisFile(SoftDeletableModel, TimeStampedModel):
    medical_history = models.OneToOneField(MedicalHistory, on_delete=models.CASCADE, related_name='disease_file')
    file = models.FileField(upload_to='diagnosis_file/', null=True, blank=True)

    class Meta:
        ordering = ['-created']

    @classmethod
    def get_or_create_file(cls, medical_history_id, diagnosis_file=None):  # None 바꿔줄 것(파일 업데이트 설계 될 시)
        diagnosis_file, _ = cls.available_objects.get_or_create(medical_history_id=medical_history_id,
                                                                defaults={
                                                                    'medical_history_id': medical_history_id,
                                                                    'file': diagnosis_file
                                                                })
        return diagnosis_file


class FundusImageLeft(SoftDeletableModel, TimeStampedModel):
    medical_history = models.OneToOneField(MedicalHistory, on_delete=models.CASCADE, related_name='fundus_image_left')
    left_image = models.ImageField(upload_to='fundus_left/', null=True, blank=True)

    class Meta:
        ordering = ['-created']

    @classmethod
    def get_or_create_fil(cls, medical_history_id, left_eye):
        fundus_image_right, _ = cls.available_objects.get_or_create(medical_history_id=medical_history_id,
                                                                    defaults={
                                                                        'medical_history_id': medical_history_id,
                                                                        'left_image': left_eye})
        return fundus_image_right


class FundusImageRight(SoftDeletableModel, TimeStampedModel):
    medical_history = models.OneToOneField(MedicalHistory, on_delete=models.CASCADE, related_name='fundus_image_right')
    right_image = models.ImageField(upload_to='fundus_right/', null=True, blank=True)

    class Meta:
        ordering = ['-created']

    @classmethod
    def get_or_create_fir(cls, medical_history_id, right_eye):
        fundus_image_right, _ = cls.available_objects.get_or_create(medical_history_id=medical_history_id,
                                                                    defaults={
                                                                        'medical_history_id': medical_history_id,
                                                                        'right_image': right_eye})
        return fundus_image_right


class DiseaseLeft(SoftDeletableModel, TimeStampedModel):
    fundus_left = models.OneToOneField(FundusImageLeft, on_delete=models.CASCADE, related_name='disease_left')
    amd = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True)
    diabetic = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True)
    glaucoma = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True)
    normal = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True)
    erm = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True, default='0')  # 추가된 컬럼

    class Meta:
        ordering = ['-created']

    @classmethod
    def get_or_create_with_condition(cls, fundus_left_id, disease_type):
        field_values = {disease: '0' for disease in CLASS_NAME_DISEASES}

        if isinstance(disease_type, list):
            for item in disease_type:
                if item in CLASS_NAME_DISEASES:
                    field_values[item] = '1'
        else:
            if disease_type in CLASS_NAME_DISEASES:
                field_values[disease_type] = '1'

        return cls.available_objects.get_or_create(
            fundus_left_id=fundus_left_id,
            defaults={},
            **field_values
        )

    def get_field_with_value_1(self):
        fields = [
            ('amd', self.amd),
            ('diabetic', self.diabetic),
            ('erm', self.erm),  # 추가된 필드
            ('glaucoma', self.glaucoma),
            ('normal', self.normal)
        ]
        print(f'fields : {fields}')
        result = [field for field, value in fields if value == "1"]
        return result if result else "normal"
        # return next((field for field, value in fields if value == "1"), None)


class DiseaseRight(SoftDeletableModel, TimeStampedModel):
    fundus_right = models.OneToOneField(FundusImageRight, on_delete=models.CASCADE, related_name='disease_right')
    amd = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True)
    diabetic = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True)
    glaucoma = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True)
    normal = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True)
    erm = models.CharField(max_length=100, choices=DANGER_LEVEL, null=True, blank=True, default='0')  # 추가된 컬럼

    class Meta:
        ordering = ['-created']

    @classmethod
    def get_or_create_with_condition(cls, fundus_right_id, disease_type):
        field_values = {disease: '0' for disease in CLASS_NAME_DISEASES}

        if isinstance(disease_type, list):
            for item in disease_type:
                if item in CLASS_NAME_DISEASES:
                    field_values[item] = '1'
        else:
            if disease_type in CLASS_NAME_DISEASES:
                field_values[disease_type] = '1'

        return cls.available_objects.get_or_create(
            fundus_right_id=fundus_right_id,
            defaults={},
            **field_values
        )

    def get_field_with_value_1(self):
        fields = [
            ('amd', self.amd),
            ('diabetic', self.diabetic),
            ('erm', self.erm),  # 추가된 필드
            ('glaucoma', self.glaucoma),
            ('normal', self.normal)
        ]
        result = [field for field, value in fields if value == "1"]
        return result if result else "normal"


class FundusHitmapImageLeft(SoftDeletableModel, TimeStampedModel):
    fundus_left = models.OneToOneField(FundusImageLeft, on_delete=models.CASCADE,
                                       related_name='fundus_hitmap_image_left')
    hit_image_left = models.ImageField(upload_to='fundus_hitmap_image_left/', null=True, blank=True)

    @classmethod
    def get_or_create_hit_left(cls, fundus_left_id, left_hit):
        fundus_hit_left, _ = cls.available_objects.get_or_create(fundus_left_id=fundus_left_id,
                                                                 defaults={
                                                                     'fundus_left_id': fundus_left_id,
                                                                     'hit_image_left': left_hit})
        return fundus_hit_left


class FundusHitmapImageRight(SoftDeletableModel, TimeStampedModel):
    fundus_right = models.OneToOneField(FundusImageRight, on_delete=models.CASCADE,
                                        related_name='fundus_hitmap_image_right')
    hit_image_right = models.ImageField(upload_to='fundus_hitmap_image_right/', null=True, blank=True)

    @classmethod
    def get_or_create_hit_right(cls, fundus_right_id, right_hit):
        fundus_hit_right, _ = cls.available_objects.get_or_create(fundus_right_id=fundus_right_id,
                                                                  defaults={
                                                                      'fundus_right_id': fundus_right_id,
                                                                      'hit_image_right': right_hit})
        return fundus_hit_right


class MemoHistory(SoftDeletableModel, TimeStampedModel):
    medical_history = models.OneToOneField(MedicalHistory, on_delete=models.CASCADE, related_name='memo_history')
    symptom_by_patient = models.TextField(null=True, blank=True)
    symptom_by_doctor = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created']

    @classmethod
    def get_or_create_memo_history(cls, medical_history_id, symptom_by_patient, memo_by_doctor):
        memo_history, _ = cls.available_objects.get_or_create(medical_history_id=medical_history_id,
                                                              defaults={
                                                                  'medical_history_id': medical_history_id,
                                                                  'symptom_by_patient': symptom_by_patient,
                                                                  'symptom_by_doctor': memo_by_doctor
                                                              })
        return memo_history


class RemovedDoctorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_removed=True)


class RemovedDoctor(Doctor):
    objects = RemovedDoctorManager()

    class Meta:
        proxy = True
        verbose_name = '삭제 처리된 의사계정'
        verbose_name_plural = '삭제 처리된 의사계정'
