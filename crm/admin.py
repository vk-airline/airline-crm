from django.contrib import admin

from .models import (
    Airport,
    Runway,
    FlightPlan,
    Flight,
    Occupation,
    Employee,
    EmployeeLog,
    Aircraft,
    AircraftDynamicInfo,
    AircraftDeviceLife,
    AircraftLog,
    SchedulersConfig
)

admin.site.register(
    (
        Airport,
        Runway,
        FlightPlan,
        Flight,
        Occupation,
        Employee,
        EmployeeLog,
        Aircraft,
        AircraftDynamicInfo,
        AircraftDeviceLife,
        AircraftLog,
        SchedulersConfig
    )
)

# Register your models here.
