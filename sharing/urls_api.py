from django.urls import path
from . import views

urlpatterns = [
    path('<str:token>/qr/', views.generate_qr_code, name='generate_qr_code'),
    path('<str:token>/info/', views.get_share_info, name='get_share_info'),
]


