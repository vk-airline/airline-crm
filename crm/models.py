from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
from timezone_field import TimeZoneField
# from cities.models import City, Country
from cities_light.models import City, Country


class Airport(models.Model):
    iata = models.CharField(max_length=3, unique=True)
    icao = models.CharField(max_length=4, unique=True)
    name = models.TextField()
    latitude = models.DecimalField(max_digits=7, decimal_places=5)
    longitude = models.DecimalField(max_digits=7, decimal_places=5)
    altitude = models.IntegerField()
    timezone = TimeZoneField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)


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
    planning_departure_time = models.TimeField()
    planning_arrival_time = models.TimeField()
    source = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="source_airport")
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="destination_airport")
    flight_code = models.CharField(max_length=255, unique=True)
    passanger_capacity = models.IntegerField()
    days_of_week = ArrayField(models.SmallIntegerField(choices=DAYS_OF_WEEK), size=7)
    start_date = models.DateField()
    end_date = models.DateField()


class Flight(models.Model):
    flight_plan = models.ForeignKey(FlightPlan, on_delete=models.CASCADE)
    planning_departure_datetime = models.DateTimeField()
    planning_arrival_datetime = models.DateTimeField()
    actual_departure_datetime = models.DateTimeField()
    actual_arrival_datetime = models.DateTimeField()
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE)
    has_arrived = models.BooleanField()
    # aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)


class Occupation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()


class Employee(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    occupation = models.ForeignKey(Occupation, on_delete=models.CASCADE)


class EmployeeLog(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    log_date = models.DateTimeField()
    description = models.JSONField()  # type: ignore
