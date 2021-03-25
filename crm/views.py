from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.utils import timezone
from django.views.generic import ListView, DetailView
from .models import Employee, EmployeeLog, Aircraft, AircraftDeviceLife
from .tasks import sleep
from django.http import HttpResponse

# Create your views here.
from django.shortcuts import render
import time


@login_required
def index(request):
    return render(request, "index.html")


def blocking(request):
    time.sleep(10)
    return HttpResponse("congratulations, you've just wasted 10 seconds of your life")


def nonblocking(request):
    sleep.delay(10)
    return HttpResponse("that was quick, wasn't it?")


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
        context['logs'] = EmployeeLog.objects.filter(
            employee=self.get_object(),
            disability_end__lte=timezone.now() + timezone.timedelta(days=30),
            disability_end__gte=timezone.now()
        ).order_by('disability_start')[:5]
        return context
