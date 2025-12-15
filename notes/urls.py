from django.urls import path
from . import views
from . import views_history

urlpatterns = [
    path('', views.editor, name='editor'),
    path('save/', views.save_note, name='save_note'),
    path('upload-image/', views.upload_image, name='upload_image'),
    path('history/<str:note_id>/', views_history.history_list, name='history_list'),
    path('history/<str:note_id>/<str:history_id>/', views_history.history_detail, name='history_detail'),
    path('history/<str:note_id>/<str:history_id>/restore/', views_history.history_restore, name='history_restore'),
    path('api/note/<str:note_id>/', views.get_note_content, name='get_note_content'),
    
    # 미디어 파일 API
    path('api/media/upload-audio/', views.upload_audio, name='upload_audio'),
    path('api/media/upload-video/', views.upload_video, name='upload_video'),
    path('api/media/files/', views.list_media_files, name='list_media_files'),
    path('api/media/files/<str:file_id>/', views.get_media_file, name='get_media_file'),
]