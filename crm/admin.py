from django.contrib import admin

from .models import (
    Airport,
    Runway,
    FlightPlan,
    Flight,
    Occupation,
    Employee,
    EmployeeLog,
)

admin.site.register((
    Airport,
    Runway,
    FlightPlan,
    Flight,
    Occupation,
    Employee,
    EmployeeLog,
))

# Register your models here.
