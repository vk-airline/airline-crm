import math
from datetime import datetime
from celery import chain
from django.contrib.auth.decorators import login_required, permission_required as p_req
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, FormView, DeleteView
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render

from rest_framework import mixins, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import FlightForm, FlightPlanForm
from .models import Employee, EmployeeLog, Aircraft, AircraftDeviceLife, AircraftLog, Flight, FlightPlan, \
    ScheduleConfig, AircraftDynamicInfo
from .tasks import check_airports_availability, generate_schedules, assign_employees, create_flights, \
    check_flights_compatibility, FlightWarning


@login_required
def index(request):
    return render(request, "index.html")


class AircraftsView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_aircraft"
    model = Aircraft
    template_name = "aircraft_list.html"


class AircraftView(PermissionRequiredMixin, DetailView):
    permission_required = "crm.view_aircraft"
    model = Aircraft
    template_name = "aircraft.html"

    def get_object(self, **kwargs):
        return Aircraft.objects.get(id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        cfg = ScheduleConfig.objects.first()
        context = super().get_context_data(**kwargs)
        aircraft = self.get_object()
        now = timezone.now()
        context['devices'] = AircraftDeviceLife.objects.filter(aircraft=aircraft)
        context['logs'] = AircraftLog.objects.filter(aircraft=aircraft).order_by('-event_datetime')
        flights = Flight.objects.filter(aircraft=self.get_object(),
                                        planning_departure_datetime__gte=now - cfg.show_past_flights_time,
                                        planning_departure_datetime__lte=now + cfg.show_future_flights_time).order_by(
            'planning_departure_datetime')
        if flights.count():
            add_flights_data_to_context(context, flights)
        return context


class AircraftsDevicesView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_aircraftdevicelife"
    model = AircraftDeviceLife
    template_name = "devices.html"


class EmployeesView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_employee"
    model = Employee
    template_name = "employee_list.html"


def add_flights_data_to_context(context, flights):
    status_dict = check_flights_compatibility(flights)

    def status_color(status):
        if status in [FlightWarning.ARRIVED, FlightWarning.SCHEDULED, FlightWarning.DEPARTED]:
            return "table-success"
        elif status in [FlightWarning.ARRIVAL_SHIFTED, FlightWarning.ARRIVAL_DELAY,
                        FlightWarning.DEPARTURE_DELAY]:
            return "table-warning"
        else:
            return "table-danger"

    context['flight_status'] = zip(flights, [
        (status_dict[flight.pk].name.replace('_', ' '), status_color(status_dict[flight.pk]))
        for flight in flights])


class FlightsView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_flight"
    model = Employee
    template_name = "flight_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = ScheduleConfig.objects.all().first()
        if not config:
            return context
        flights = Flight.objects.filter(
            planning_departure_datetime__gte=timezone.now() - config.show_past_flights_time,
            planning_departure_datetime__lte=timezone.now() + config.show_future_flights_time
        ).order_by('planning_departure_datetime')
        add_flights_data_to_context(context, flights)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = list(e for e in Flight.objects.get(pk=self.kwargs['pk']).employees.all())
        return context

    def form_valid(self, form):
        # Logic that checks updates
        form.save()
        return HttpResponseRedirect(self.success_url)


class FlightDelete(DeleteView):
    model = Flight
    success_url = reverse_lazy('crm:flights')
    template_name = 'confirm_delete.html'


class FlightPlansView(PermissionRequiredMixin, ListView):
    permission_required = "crm.view_flightplan"
    model = FlightPlan
    template_name = "flightplan_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = FlightPlan.objects.all().order_by('start_date', 'planning_departure_time')
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
    template_name = "confirm_delete.html"


class EmployeeView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = "employee.html"

    def get_object(self, **kwargs):
        return Employee.objects.get(id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        config = ScheduleConfig.objects.first()
        context = super().get_context_data(**kwargs)
        context['logs'] = EmployeeLog.objects.filter(
            employee=self.get_object(),
            disability_end__lte=timezone.now() + timezone.timedelta(days=30),
            disability_end__gte=timezone.now()
        ).order_by('disability_start')[:5]
        flights = Flight.objects.filter(
            employees__in=[self.get_object()],
            planning_departure_datetime__gte=timezone.now() - config.show_past_flights_time,
            planning_departure_datetime__lte=timezone.now() + config.show_future_flights_time
        ).order_by('planning_departure_datetime')

        add_flights_data_to_context(context, flights)
        return context


class FlightDeparture(APIView):
    def get_object(self, pk):
        try:
            return Flight.objects.get(pk=pk)
        except Flight.DoesNotExist:
            raise Http404

    def post(self, request, pk):
        flight = self.get_object(pk)
        if flight.actual_departure_datetime or flight.actual_arrival_datetime:
            return Response(status=status.HTTP_409_CONFLICT)

        flight.actual_departure_datetime = datetime.fromisoformat(
            request.data['actual_departure_datetime'])
        flight.save()
        flight.aircraft.departed()
        return Response(status=status.HTTP_200_OK)


class FlightArrival(APIView):
    def get_object(self, pk):
        try:
            return Flight.objects.get(pk=pk)
        except Flight.DoesNotExist:
            raise Http404

    def post(self, request, pk):
        flight = self.get_object(pk)
        if not flight.actual_departure_datetime or flight.actual_arrival_datetime:
            return Response(status=status.HTTP_409_CONFLICT)

        flight.actual_arrival_datetime = datetime.fromisoformat(
            request.data['actual_arrival_datetime'])
        flight.save()

        hours_flown = math.ceil((flight.actual_arrival_datetime -
                                 flight.actual_arrival_datetime).total_seconds() / 3600)
        if hours_flown < 0:
            return Response(status=status.HTTP_409_CONFLICT)

        flight.aircraft.landed(hours_flown)
        return Response(status=status.HTTP_200_OK)


class FuelView(APIView):
    def get_object(self, pk):
        try:
            return AircraftDynamicInfo.objects.get(aircraft=pk)
        except AircraftDynamicInfo.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        dyinfo = self.get_object(pk)
        return Response({"fuel_remaining_kg": dyinfo.fuel_remaining_kg}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        dyinfo = self.get_object(pk)
        dyinfo.update_fuel(request.data["fuel_remaining_kg"])
        return Response(status=status.HTTP_200_OK)
