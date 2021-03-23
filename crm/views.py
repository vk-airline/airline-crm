from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import ListView
from .models import Employee, Aircraft, AircraftDeviceLife

# Create your views here.
from django.shortcuts import render


@login_required
def index(request):
    return render(request, "index.html")


class AircraftsView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_aircraft"
    model = Aircraft
    template_name = "aircrafts.html"


class AircraftsDevicesView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_aircraftdevicelife"
    model = AircraftDeviceLife
    template_name = "devices.html"


class EmployeesView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = "employees.html"
