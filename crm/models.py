from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from timezone_field import TimeZoneField
from multiselectfield import MultiSelectField


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
    FLIGHT_PLAN_CHOICES = (
        (0, "Pending"),
        (1, "Processing FPM"),
        (2, "Error FPM"),
        (3, "Pending EPM"),
        (4, "Processing EPM"),
        (5, "Error EPM"),
        (6, "Success")
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
    status = models.SmallIntegerField(choices=FLIGHT_PLAN_CHOICES, default=0)
    description = models.TextField(default="", blank=True)

    def get_absolute_url(self):
        return reverse("edit flight plan", kwargs={'pk': self.pk})

    def __str__(self):
        return self.flight_code


class Occupation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    occupation = models.ForeignKey(Occupation, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class EmployeeLog(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    disability_start = models.DateTimeField(null=True)
    disability_end = models.DateTimeField(null=True)
    description = models.CharField(max_length=1024)


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


class AircraftDynamicInfo(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    economy_class_cap = models.PositiveSmallIntegerField()
    business_class_cap = models.PositiveSmallIntegerField()
    first_class_cap = models.PositiveSmallIntegerField()
    fuel_remaining_kg = models.PositiveIntegerField()


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
    has_arrived = models.BooleanField()
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse("crm:edit flight", kwargs={'pk': self.pk})
