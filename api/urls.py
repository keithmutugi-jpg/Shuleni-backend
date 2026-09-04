from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check),
    path('schools/register/', views.register_school),
    path('auth/login/', views.login_view),
    path('auth/logout/', views.logout_view),
    path('auth/session/', views.session_view),
    path('users/', views.users_view),
    path('resources/', views.resources_view),
    path('attendance/', views.attendance_view),
    path('attendance/submit/', views.attendance_submit_view),
    path('exams/', views.exams_view),
    path('exams/<int:exam_id>/submit/', views.exam_submit_view),
    path('exam-results/', views.exam_results_view),
    path('chats/', views.chats_view),
    path('chats/<int:room_id>/messages/', views.chat_message_view),
]
