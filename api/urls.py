from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health_check),
    path('schools/register/', views.register_school),
    path('auth/login/', views.login_view),
    path('auth/logout/', views.logout_view),
    path('auth/session/', views.session_view),
    path('users/', views.users_view),
]