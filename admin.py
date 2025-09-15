from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from import_export import resources, fields
from import_export.admin import ExportActionMixin, ImportMixin, ImportExportActionModelAdmin, ImportExportModelAdmin
from import_export.formats.base_formats import XLSX

from core.admin import SoftDeletableAdmin
from core.utils import mask_korean_name, mask_account, masked_reg_no
from doctors.admin_method import HistoryChecker, PermissionControlMixin
from doctors.models import (Doctor, DoctorInfo, Patient, PatientInfo, MedicalHistory, RemovedDoctor, DiseaseLeft,
                            DiseaseRight,
                            )


# Register your models here.
# admin.site.register(DiseaseLeft)
# admin.site.register(DiseaseRight)

class DoctorResource(resources.ModelResource):
    class Meta:
        model = Doctor


class MedicalHistoryInline(PermissionControlMixin, admin.TabularInline):
    model = MedicalHistory
    extra = 1
    readonly_fields = ['link', 'created']
    fields = ['link', 'created']
    list_display = ['link', 'created']

    def link(self, obj):
        if obj.pk:
            url = reverse('admin:doctors_medicalhistory_change', args=[obj.pk])
            return format_html('<a href="{}">link to history data</a>', url, obj.pk)
        else:
            return None

    link.short_description = 'Medical History Link'


class PatientInfoInline(PermissionControlMixin, admin.TabularInline):
    model = PatientInfo
    extra = 1
    list_display = ('name', 'age', 'gender')

    def name(self, obj):
        return f"{mask_korean_name(obj.patient_info.name)}"

    def age(self, obj):
        return f"{obj.patient_info.age}"

    def gender(self, obj):
        return f"{obj.patient_info.gender}"


class PatientInline(PermissionControlMixin, admin.TabularInline):
    model = Patient
    extra = 1
    fields = ('patient_reg_no_masked', 'patient_info', 'link')
    readonly_fields = ('patient_reg_no_masked', 'patient_info', 'link')
    inlines = [PatientInfo, ]

    def link(self, obj):
        if obj.pk:
            url = reverse('admin:doctors_patient_change', args=[obj.pk])
            return format_html('<a href="{}">link to doctors patient</a>', url, obj.pk)
        else:
            return None

    def patient_reg_no_masked(self, obj):
        if obj:
            masked = masked_reg_no(obj)
            return masked
        return "No reg_no"


class DoctorInfoInline(PermissionControlMixin, admin.TabularInline):
    model = DoctorInfo
    extra = 1
    fields = ('doctor', 'name')


@admin.register(Doctor)
class DoctorAdmin(PermissionControlMixin, SoftDeletableAdmin):
    resource_class = DoctorResource
    list_display = ('의사계정', 'omitted_name', '유효기한')
    readonly_fields = ('의사계정', 'omitted_name', '유효기한')
    search_fields = ['user__account']
    search_help_text = '계정 검색'
    inlines = [PatientInline, DoctorInfoInline]

    def 의사계정(self, obj):
        return f'{mask_account(obj.user.account)}'

    def omitted_name(self, obj):
        nickname = mask_korean_name(obj.doctor_info.name)
        return f"{nickname}"

    def 유효기한(self, obj):
        from datetime import timedelta
        return obj.created + timedelta(days=365)

    def get_fieldsets(self, request, obj=None):
        return [(None, {'fields': ('omitted_name',)})]


@admin.register(RemovedDoctor)
class RemovedDoctorAdmin(PermissionControlMixin, SoftDeletableAdmin):
    list_display = ('의사계정', 'omitted_name')
    readonly_fields = ('의사계정', 'omitted_name')
    search_fields = ['user__account']
    search_help_text = '계정 검색'
    inlines = [PatientInline, DoctorInfoInline]

    def 의사계정(self, obj):
        return f'{mask_account(obj.user.account)}'

    def omitted_name(self, obj):
        nickname = mask_korean_name(obj.doctor_info.name)
        return f"{nickname}"

    def get_fieldsets(self, request, obj=None):
        return [(None, {'fields': ('omitted_name',)})]


@admin.register(Patient)
class PatientAdmin(PermissionControlMixin, SoftDeletableAdmin):
    inlines = [MedicalHistoryInline, ]

    def get_fieldsets(self, request, obj=None):
        return [(None, {'fields': ('patient_reg_no_masked',)})]

    def patient_reg_no_masked(self, obj):
        if obj:
            masked = masked_reg_no(obj)
            return masked
        return "No reg_no"


class MedicalHistoryResource(resources.ModelResource):
    created = fields.Field(attribute='created', column_name='생성일')
    modified = fields.Field(attribute='modified', column_name='수정일')
    # Using a custom method to retrieve the patient name
    patient_name = fields.Field(attribute='patient_name', column_name='환자성함')
    좌안 = fields.Field(column_name='좌안')
    우안 = fields.Field(column_name='우안')
    좌안히트맵 = fields.Field(column_name='좌안 히트맵')
    우안히트맵 = fields.Field(column_name='우안 히트맵')
    좌안병변 = fields.Field(column_name='좌안 병변')
    우안병변 = fields.Field(column_name='우안 병변')
    방문일자 = fields.Field(column_name='방문일자')
    메모 = fields.Field(column_name='메모')

    class Meta:
        model = MedicalHistory
        fields = ('patient_name', 'created', 'modified', '방문일자', '좌안', '우안', '좌안히트맵', '우안히트맵', '좌안병변', '우안병변', '메모')

    def dehydrate_patient_name(self, record):
        return record.patient.patient_info.name if record.patient and record.patient.patient_info else "알 수 없음"

    def dehydrate_방문일자(self, record):
        return record.created.strftime("%Y년 %m월 %d일 %H시")

    def dehydrate_좌안(self, record):
        return HistoryChecker.check_image(record.fundus_image_left.left_image)

    def dehydrate_우안(self, record):
        return HistoryChecker.check_image(record.fundus_image_right.right_image)

    def dehydrate_좌안히트맵(self, record):
        return HistoryChecker.check_image(record.fundus_image_left.fundus_hitmap_image_left.hit_image_left)

    def dehydrate_우안히트맵(self, record):
        return HistoryChecker.check_image(record.fundus_image_right.fundus_hitmap_image_right.hit_image_right)

    def dehydrate_좌안병변(self, record):
        return HistoryChecker.check_disease(record.fundus_image_left.disease_left)

    def dehydrate_우안병변(self, record):
        return HistoryChecker.check_disease(record.fundus_image_right.disease_right)

    def dehydrate_메모(self, record):
        if not record.memo_history:
            return "없음"
        if record.memo_history.symptom_by_patient or record.memo_history.symptom_by_doctor:
            return "있음"
        return "없음"

    def dehydrate_patient_name(self, record):
        return record.patient.patient_info.name.encode("utf-8").decode("utf-8")


@admin.register(MedicalHistory)
class MedicalHistory(PermissionControlMixin, ImportExportModelAdmin):
    resource_class = MedicalHistoryResource
    list_display = HistoryChecker.get_history_child()
    fields = HistoryChecker.get_history_child()
    readonly_fields = HistoryChecker.get_history_child()
    formats = [XLSX]  # ✅ XLSX 활성화

    def 환자이름(self, obj):
        return f'{mask_account(obj.patient.patient_info.name)}'

    def 방문일자(self, obj):
        return obj.created.strftime("%Y년 %m월 %d일 %H시")

    def 좌안(self, obj):
        return HistoryChecker.check_image(obj.fundus_image_left.left_image)

    def 우안(self, obj):
        return HistoryChecker.check_image(obj.fundus_image_right.right_image)

    def 좌안히트맵(self, obj):
        return HistoryChecker.check_image(obj.fundus_image_left.fundus_hitmap_image_left.hit_image_left)

    def 우안히트맵(self, obj):
        return HistoryChecker.check_image(obj.fundus_image_right.fundus_hitmap_image_right.hit_image_right)

    def 좌안병변(self, obj):
        return HistoryChecker.check_disease(obj.fundus_image_left.disease_left)

    def 우안병변(self, obj):
        return HistoryChecker.check_disease(obj.fundus_image_right.disease_right)

    def 메모(self, obj):
        if not obj.memo_history:
            return "없음"
        if obj.memo_history.symptom_by_patient or obj.memo_history.symptom_by_doctor:
            return "있음"
        return "없음"

    for field, short_description in HistoryChecker.get_short_descriptions().items():
        setattr(MedicalHistory, field, short_description)
