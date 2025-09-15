# django
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
# core
from core.decorator import is_doctor_required
from doctors.models import Patient, PatientInfo
# apps
from doctors.views_util import get_patients, get_patients_detail, get_patients_history_result, save_diagnosis_info


@login_required(login_url="/users/prepare_login/")
@is_doctor_required
@require_http_methods(["GET"])
def show_patients(request, doctor_pk):
    doctor_pk = request.user.doctor.id
    context = get_patients(request.META.get("QUERY_STRING"), doctor_pk)
    return render(request, 'doctors/patients.html', context)


@is_doctor_required
@login_required(login_url="/users/prepare_login/")
@require_http_methods(["GET"])
def show_patients_detail(request, doctor_pk, patient_pk):
    context = get_patients_detail(request.META.get("QUERY_STRING"), patient_pk)
    return render(request, 'doctors/patients_detail.html', context=context)


@is_doctor_required
@login_required(login_url="/users/prepare_login/")
@require_http_methods(["GET"])
def show_patients_history_result(request, doctor_pk, patient_pk, history_pk):
    context = get_patients_history_result(patient_pk, history_pk)
    return render(request, 'doctors/diagnose-result.html', context=context)


@is_doctor_required
@login_required(login_url="/users/prepare_login/")
@require_http_methods(["POST"])
def diagnose_result(request, doctor_pk):
    context = save_diagnosis_info(request, doctor_pk)

    # save_diagnosis_info가 오류 dict를 반환한 경우
    if context.get("status") == "error":
        # 예: 에러 페이지 렌더링 또는 동일 페이지에 에러 메시지 표시
        return redirect("main")

    # 정상적으로 dict 형식의 결과를 반환한 경우
    return render(request, 'doctors/diagnose-result.html', context)


@is_doctor_required
def get_diagnose_template(request, doctor_pk):
    check_patient_url = '/doctors/getpatientsinfo/'
    return render(request, 'doctors/diagnose.html', {'check_patient_url': check_patient_url})


def get_patients_info(request):
    """
    주어진 reg_no와 request.user.account를 기반으로 환자 정보를 조회하여 JSON 응답을 반환합니다.
    환자 정보가 없거나 reg_no가 제공되지 않으면 적절한 오류 메시지를 반환합니다.
    """
    from django.db.models import Q
    from django.http import JsonResponse
    reg_no = request.GET.get("reg_no", "").strip()
    if not reg_no:
        return JsonResponse({"error": "Registration number is missing."}, status=400)

    # 사용자 계정과 결합한 등록번호 생성
    combined_reg_no = f"{reg_no}_{request.user.account}"

    # Patient 모델에서 combined_reg_no 또는 reg_no가 일치하고, 해당 의사의 환자인 항목을 조회
    patient_qs = Patient.objects.filter(
        Q(patient_reg_no=combined_reg_no) | Q(patient_reg_no=reg_no),
        doctor_id=request.user.doctor.id
    )

    if not patient_qs.exists():
        return JsonResponse({"error": "Patient not found."}, status=404)

    patient = patient_qs.first()

    try:
        patient_info = PatientInfo.objects.get(patient=patient)
    except PatientInfo.DoesNotExist:
        return JsonResponse({"error": "Patient information not found."}, status=404)

    context = {
        "name": patient_info.name,
        "birth": patient_info.age,  # 만약 birth가 생년월일이면, 변수명 수정 고려
        "gender": patient_info.gender,
    }
    return JsonResponse(context)

def brain(request):
    return render(request, 'doctors/brain.html')