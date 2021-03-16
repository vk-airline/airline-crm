from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('aircrafts', views.aircrafts_view, name='aircrafts'),
    path('aircrafts_devices', views.aircrafts_devices, name='aircrafts devices'),
]
