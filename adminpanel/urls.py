from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('notes/', views.notes_list, name='admin_notes_list'),
    path('notes/<str:note_id>/expire/', views.note_expire, name='admin_note_expire'),
    path('notes/<str:note_id>/delete/', views.note_delete, name='admin_note_delete'),
    path('notes/<str:note_id>/history/', views.note_history_list, name='admin_note_history_list'),
]