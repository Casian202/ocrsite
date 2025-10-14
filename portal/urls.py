from django.urls import path

from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('descarca/<uuid:job_id>/', views.download_job, name='download'),
]
