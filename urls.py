from django.urls import path

from doctors import views

app_name = "doctors"

urlpatterns = [
    path(r'<uuid:doctor_pk>/patients/', views.show_patients, name='show_patients'),
    path(r'<uuid:doctor_pk>/patients/detail/<uuid:patient_pk>/', views.show_patients_detail, name='show_patients_detail'),
    path(r'<uuid:doctor_pk>/diagnose/', views.get_diagnose_template, name='get_diagnose_template'),
    path(r'<uuid:doctor_pk>/diagnose/result/', views.diagnose_result, name='diagnose_result'),
    path(r'<uuid:doctor_pk>/patients/detail/<uuid:patient_pk>/result/<uuid:history_pk>/', views.show_patients_history_result, name='show_patients_history_result'),
    path(r'getpatientsinfo/', views.get_patients_info, name='get_patients_info'),
    path(r'brain/', views.brain, name='brain'),
]
