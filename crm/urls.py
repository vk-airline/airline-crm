from django.urls import path
from crm.views import *

app_name = "crm"
urlpatterns = [
    path('', index, name='index'),
    path('blocking/', blocking, name="celery test"),
    path('nonblocking/', nonblocking, name="celery test2"),
    path('aircrafts', AircraftsView.as_view(), name='aircrafts'),
    path('aircrafts/<int:pk>', AircraftView.as_view(), name='aircraft view'),
    path('aircrafts_devices/', AircraftsDevicesView.as_view(), name='aircrafts devices'),
    path('employees', EmployeesView.as_view(), name='employees'),
    path('employees/<int:pk>/', EmployeeView.as_view(), name='employee view'),
]
