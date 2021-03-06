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
    ScheduleConfig
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
        ScheduleConfig
    )
)

# Register your models here.
