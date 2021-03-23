from django.urls import path
from crm.views import index, AircraftsView, AircraftsDevicesView, EmployeesView

app_name = "crm"
urlpatterns = [
    path('', index, name='index'),
    path('aircrafts', AircraftsView.as_view(), name='aircrafts'),
    path('aircrafts_devices/', AircraftsDevicesView.as_view(), name='aircrafts devices'),
    path('employees', EmployeesView.as_view(), name='employees')
]
