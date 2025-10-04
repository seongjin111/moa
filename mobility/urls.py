from django.urls import path
from . import views

urlpatterns = [
    path("route/", views.route_page, name="route_page"),
    path("api/route/", views.route_to_stop, name="api_route_to_stop"),
]
