from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.utils import timezone
from django.views.generic import ListView, DetailView
from .models import Employee, EmployeeLog, Aircraft, AircraftDeviceLife

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


class EmployeeView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = "employee.html"

    def get_object(self, **kwargs):
        return Employee.objects.get(id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disabilities'] = EmployeeLog.objects.filter(employee=self.get_object(),
                                                             disability_end__gte=timezone.now()).order_by(
            'disability_start')
        return context
