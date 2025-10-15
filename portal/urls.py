from django.urls import path

from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.home, name='home'),
    path('inregistrare/', views.signup, name='signup'),
    path('ocr/', views.ocr_studio, name='ocr'),
    path('ocr/descarca/<uuid:job_id>/', views.download_job, name='download_job'),
    path('ocr/sidecar/<uuid:job_id>/', views.download_sidecar, name='download_sidecar'),
    path('ocr/folder/<uuid:job_id>/', views.assign_job_folder, name='assign_job_folder'),
    path('ocr/sterge/<uuid:job_id>/', views.delete_job, name='delete_job'),
    path('biblioteci/', views.libraries, name='libraries'),
    path('biblioteci/<uuid:folder_id>/', views.library_detail, name='library_detail'),
    path(
        'biblioteci/<uuid:folder_id>/descarca/',
        views.download_library_archive,
        name='download_library_archive',
    ),
    path('previzualizare/', views.preview_hub, name='preview_hub'),
    path('previzualizare/<uuid:document_id>/', views.preview_document, name='preview'),
    path('previzualizare/<uuid:document_id>/descarca/', views.download_document, name='download_document'),
    path('word/', views.word_studio, name='word'),
    path('word/<uuid:document_id>/descarca/', views.download_word_document, name='download_word'),
    path('admin-console/', views.admin_console, name='admin'),
]
