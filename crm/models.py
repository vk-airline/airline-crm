from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.timezone import make_aware
from timezone_field import TimeZoneField
from multiselectfield import MultiSelectField
from django.db.models import Q


class ScheduleConfig(models.Model):
    show_past_flights_time = models.DurationField()
    show_future_flights_time = models.DurationField()

    warning_schedule_delay_time = models.DurationField()
    warning_arrival_delay_time = models.DurationField()
    warning_arrival_shifted_time = models.DurationField()

    min_between_flights_delay_minutes = models.DurationField()
    max_flight_generation_attempts = models.PositiveSmallIntegerField()
    flight_generation_timeout = models.DurationField()


class Airport(models.Model):
    iata = models.CharField(max_length=3, unique=True)
    icao = models.CharField(max_length=4, unique=True)
    name = models.TextField()
    latitude = models.DecimalField(max_digits=7, decimal_places=5)
    longitude = models.DecimalField(max_digits=7, decimal_places=5)
    altitude = models.IntegerField()
    timezone = TimeZoneField()
    country = models.CharField(max_length=255)
    city = models.CharField(max_length=255)

    def __str__(self):
        return self.name


RUNWAY_CATEGORIES = (
    (0, "I"),
    (1, "II"),
    (2, "IIIA"),
    (3, "IIIB"),
)


class Runway(models.Model):
    airport = models.ForeignKey(Airport, on_delete=models.CASCADE)
    length = models.IntegerField()
    category = models.SmallIntegerField(choices=RUNWAY_CATEGORIES)
    is_active = models.BooleanField()


DAYS_OF_WEEK = (
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
)


class FlightPlan(models.Model):
    PENDING = 0
    PROCESSING_FPM = 1
    ERROR_FPM = 2
    PENDING_EPM = 3
    PROCESSING_EPM = 4
    ERROR_EPM = 5
    SUCCESS = 6
    FLIGHT_PLAN_CHOICES = (
        (PENDING, "Pending"),
        (PROCESSING_FPM, "Processing FPM"),
        (ERROR_FPM, "Error FPM"),
        (PENDING_EPM, "Pending EPM"),
        (PROCESSING_EPM, "Processing EPM"),
        (ERROR_EPM, "Error EPM"),
        (SUCCESS, "Success")
    )
    planning_departure_time = models.TimeField()
    planning_arrival_time = models.TimeField()
    source = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="source_airport")
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="destination_airport")
    flight_code = models.CharField(max_length=255, unique=True)
    passanger_capacity = models.PositiveSmallIntegerField()
    days_of_week = MultiSelectField(choices=DAYS_OF_WEEK)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.SmallIntegerField(choices=FLIGHT_PLAN_CHOICES, default=PENDING)
    description = models.TextField(default="", blank=True)

    def get_absolute_url(self):
        return reverse("edit flight plan", kwargs={'pk': self.pk})

    def __str__(self):
        return f"flight plan {self.flight_code}"


class Occupation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    occupation = models.ForeignKey(Occupation, on_delete=models.CASCADE)

    def planned_location_at(self, date):
        # Get the last known flight that flies out before date
        flights = Flight.objects.filter(
            canceled=False,
            employees__in=[self],
            planning_departure_datetime__lte=date).order_by('-planning_arrival_datetime')
        if not flights:
            return Airport.objects.none()
        # if there are any get the planned destination
        return flights[0].flight_plan.destination

    # checks whether or not an employee is available in range
    # start_date <= is_available? < end_date
    def is_available(self, start_datetime, end_datetime):
        # if query returns something then employee is not available
        # at some point in the range
        query = Q(employee=self) & ~Q(status=EmployeeLog.OK) & (
            (Q(disability_end__gte=start_datetime) & Q(disability_start__lt=end_datetime))
        )
        return not bool(EmployeeLog.objects.filter(query))

    def __str__(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username


class EmployeeLog(models.Model):
    OK = 0
    NO_SHOW = 1
    LEAVE_UNPAID = 2
    LEAVE_PAID = 3
    LEAVE_SICK = 4
    EMPLOYEE_LOG_STATES = (
        (OK, "OK"),
        (NO_SHOW, "NO-SHOW"),
        (LEAVE_UNPAID, "LEAVE UNPAID"),
        (LEAVE_PAID, "LEAVE PAID"),
        (LEAVE_SICK, "LEAVE SICK"),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    disability_start = models.DateTimeField(null=True)
    disability_end = models.DateTimeField(null=True)
    status = models.SmallIntegerField(
        choices=EMPLOYEE_LOG_STATES, default=EMPLOYEE_LOG_STATES[0])
    description = models.CharField(max_length=1024, null=True)

    def __str__(self):
        return str(self.employee) + ' ' + self.EMPLOYEE_LOG_STATES[self.status][1]


class Aircraft(models.Model):
    tail_code = models.TextField(max_length=10)
    aircraft_model = models.TextField(max_length=255)
    mtow_weight_kg = models.PositiveIntegerField()
    max_payload_kg = models.PositiveIntegerField()
    range_of_flight_km = models.PositiveSmallIntegerField()
    cargo_volume_m = models.PositiveSmallIntegerField()
    fuel_capacity_kg = models.PositiveIntegerField()
    takeoff_length_m = models.PositiveIntegerField()
    landing_length_m = models.PositiveIntegerField()
    speed_kmh = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.tail_code

    def departed(self):
        for device in self.aircraftdevicelife_set.all():
            device.depart_update()

    def landed(self, hours_flown):
        for device in self.aircraftdevicelife_set.all():
            device.land_update(hours_flown)


class AircraftDynamicInfo(models.Model):
    aircraft = models.OneToOneField(Aircraft, on_delete=models.CASCADE)
    economy_class_cap = models.PositiveSmallIntegerField()
    business_class_cap = models.PositiveSmallIntegerField()
    first_class_cap = models.PositiveSmallIntegerField()
    pilots_number = models.PositiveSmallIntegerField(default=1)
    attendants_number = models.PositiveSmallIntegerField(default=0)
    fuel_remaining_kg = models.PositiveIntegerField()

    def update_fuel(self, fuel_kg):
        self.fuel_remaining_kg = fuel_kg
        self.save()

class AircraftDeviceLife(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    device_name = models.CharField(max_length=1024)
    latest_update = models.DateTimeField()
    max_operation_time_h = models.PositiveIntegerField()
    max_operation_cycles = models.PositiveIntegerField()
    total_operation_time_h = models.PositiveIntegerField()
    total_operation_cycles = models.PositiveIntegerField()
    after_service_time_h = models.PositiveIntegerField()
    after_service_cycles = models.PositiveIntegerField()
    service_time_period_h = models.PositiveIntegerField()
    service_cycles_period = models.PositiveIntegerField()

    def depart_update(self):
        self.total_operation_cycles += 1
        self.after_service_cycles += 1
        self.latest_update = make_aware(datetime.now())
        self.save()

    def land_update(self, hours_flown):
        self.total_operation_time_h += hours_flown
        self.after_service_time_h += hours_flown
        self.latest_update = make_aware(datetime.now())
        self.save()

    def __str__(self):
        return str(self.aircraft) + ' ' + self.device_name

AIRCRAFT_EVENT_STATUS = ((0, "Can fly with passengers"), (1, "Can fly without passengers"), (2, "Can't fly at all"))


class AircraftLog(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT)
    event_datetime = models.DateTimeField()
    event_description = models.TextField()
    event_type = models.SmallIntegerField(choices=AIRCRAFT_EVENT_STATUS)


class Flight(models.Model):
    flight_plan = models.ForeignKey(FlightPlan, on_delete=models.CASCADE)
    planning_departure_datetime = models.DateTimeField()
    planning_arrival_datetime = models.DateTimeField()
    actual_departure_datetime = models.DateTimeField(blank=True, null=True)
    actual_arrival_datetime = models.DateTimeField(blank=True, null=True)
    actual_destination = models.ForeignKey(Airport, blank=True, null=True, on_delete=models.CASCADE)
    canceled = models.BooleanField(default=False)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    employees = models.ManyToManyField(Employee)

    def get_absolute_url(self):
        return reverse("crm:edit flight", kwargs={'pk': self.pk})

    def __str__(self):
        return f"flight {str(self.pk)}"
