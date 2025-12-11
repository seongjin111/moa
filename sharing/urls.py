from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_share, name='create_share'),
    path('<str:token>/change-password/', views.change_password, name='change_password'),
    path('<str:token>/edit/', views.edit_share, name='edit_share'),
    path('<str:token>/', views.view_share, name='view_share'),
]