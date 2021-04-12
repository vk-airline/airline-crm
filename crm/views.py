from celery import chain
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, FormView, DeleteView

from .forms import FlightForm, FlightPlanForm
from .models import Employee, EmployeeLog, Aircraft, AircraftDeviceLife, AircraftLog, Flight, FlightPlan
from .tasks import check_airports_availability, generate_schedules, assign_employees, create_flights
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render


@login_required
def index(request):
    return render(request, "index.html")


class AircraftsView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_aircraft"
    model = Aircraft
    template_name = "aircrafts.html"


class AircraftView(PermissionRequiredMixin, DetailView):
    permission_required = "crm.view_aircraft"
    model = Aircraft
    template_name = "aircraft.html"

    def get_object(self, **kwargs):
        return Aircraft.objects.get(id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aircraft = self.get_object()
        context['devices'] = AircraftDeviceLife.objects.filter(aircraft=aircraft)
        context['logs'] = AircraftLog.objects.filter(aircraft=aircraft).order_by('-event_datetime')
        return context


class AircraftsDevicesView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_aircraftdevicelife"
    model = AircraftDeviceLife
    template_name = "devices.html"


class EmployeesView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_employee"
    model = Employee
    template_name = "employees.html"


class FlightsView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_flight"
    model = Employee
    template_name = "flights.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flights'] = Flight.objects.filter(
            planning_departure_datetime__gte=timezone.now() - timezone.timedelta(days=7),
            planning_departure_datetime__lte=timezone.now() + timezone.timedelta(days=31)
        ).order_by('planning_departure_datetime')
        return context


class FlightView(PermissionRequiredMixin, FormView):
    permission_required = "crm.view_flight"
    form_class = FlightForm
    success_url = reverse_lazy("crm:flights")
    template_name = 'flight.html'

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        if 'pk' in self.kwargs:
            form_kwargs['instance'] = Flight.objects.get(pk=int(self.kwargs['pk']))
        return form_kwargs

    def form_valid(self, form):
        # Logic that checks updates
        form.save()
        return HttpResponseRedirect(self.success_url)


class FlightDelete(DeleteView):
    model = Flight
    success_url = reverse_lazy('crm:flights')
    template_name = 'flight_confirm_delete.html'


class FlightPlansView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_flightplan"
    model = FlightPlan
    template_name = "flightplans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = FlightPlan.objects.filter(
            end_date__gte=timezone.now() - timezone.timedelta(days=1),
        ).order_by('start_date')
        return context


class FlightPlanView(PermissionRequiredMixin, FormView):
    permission_required = "crm.view_flightplan"
    form_class = FlightPlanForm
    success_url = reverse_lazy("crm:flight plans")
    template_name = 'flightplan.html'

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        if 'pk' in self.kwargs:
            form_kwargs['instance'] = FlightPlan.objects.get(pk=int(self.kwargs['pk']))
        return form_kwargs

    def form_valid(self, form):
        if form.instance.status == FlightPlan.PENDING:  # pending
            form.save()
            chain(generate_schedules.s(timezone.now().isoformat()) |
                  assign_employees.s() |
                  create_flights.s()
                  ).delay()
            return HttpResponseRedirect(self.success_url)
        return HttpResponse("You can't change status")


class FlightPlanDelete(DeleteView):
    model = FlightPlan
    success_url = reverse_lazy('crm:flight plans')
    template_name = 'flightplan_confirm_delete.html'


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
