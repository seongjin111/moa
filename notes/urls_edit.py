from django.urls import path
from . import views_edit

urlpatterns = [
    path('<str:note_id>/', views_edit.edit_page, name='edit_page'),
]