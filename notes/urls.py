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
]