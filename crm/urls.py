from django.urls import path
from crm.views import AircraftsDevicesView, AircraftView, EmployeeView, EmployeesView, FlightPlanView, \
    FlightPlansView, FlightsView, index, AircraftsView, FlightView, FlightPlanDelete, FlightDelete

app_name = "crm"
urlpatterns = [
    path('', index, name='index'),
    path('aircrafts', AircraftsView.as_view(), name='aircrafts'),
    path('aircrafts/<int:pk>', AircraftView.as_view(), name='aircraft view'),
    path('aircrafts_devices/', AircraftsDevicesView.as_view(), name='aircrafts devices'),
    path('employees', EmployeesView.as_view(), name='employees'),
    path('employees/<int:pk>/', EmployeeView.as_view(), name='employee view'),
    path('flights/', FlightsView.as_view(), name='flights'),
    path('flights/<int:pk>/delete/', FlightDelete.as_view(), name='delete flight'),
    path('flights/<int:pk>', FlightView.as_view(), name='edit flight'),
    path('flightplans/', FlightPlansView.as_view(), name='flight plans'),
    path('flightplans/<int:pk>', FlightPlanView.as_view(), name='edit flight plan'),
    path('flightplans/<int:pk>/delete/', FlightPlanDelete.as_view(), name='delete flight plan'),
    path('flightplans/add', FlightPlanView.as_view(), name='add flight plan')
]
