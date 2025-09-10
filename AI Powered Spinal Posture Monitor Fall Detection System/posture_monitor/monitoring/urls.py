from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('monitoring/', views.real_time_monitoring, name='real_time_monitoring'),
    path('offline/', views.offline_analysis, name='offline_analysis'),
    path('settings/', views.settings, name='settings'),
    path('api/upload-offline-data/', views.upload_offline_data, name='upload_offline_data'),
    path('api/posture-history/', views.api_posture_history, name='posture_history'),
]