from datetime import datetime, timezone
from django.test import TestCase
from .models import Employee, Airport
from .tasks import assign_employees


class EmployeeModelTest(TestCase):
    fixtures = [
        "auth.Group.json",
        "auth.User.json",
        "crm.Occupation.json",
        "crm.Employee.json",
        "crm.Aircraft.json",
        "crm.Airport.json",
        "crm.FlightPlan.json",
        "crm.Flights.json",
    ]

    def test_planned_location_at(self):
        empl = Employee.objects.get(id=4)
        date = datetime.fromisoformat("2021-04-27T06:00:00+00:00")
        loc = empl.planned_location_at(date)
        self.assertEquals(loc, Airport.objects.get(id=1))

        date2 = datetime.fromisoformat("2021-04-25T06:00:00+00:00")
        loc2 = empl.planned_location_at(date2)
        self.assertFalse(loc2.exists())


class AssignEmployeesTest(TestCase):
    fixtures = [
        "auth.Group.json",
        "auth.User.json",
        "crm.Occupation.json",
        "crm.Employee.json",
        # "crm.EmployeeLog.json",
        "crm.Aircraft.json",
        "crm.Airport.json",
        "crm.FlightPlan.json",
        "crm.AircraftDynamicInfo.json",
    ]

    def test_assign_employees(self):
        self.maxDiff = None
        start_date = datetime(2021, 4, 26, 0, 0, tzinfo=timezone.utc)
        schedule_variants = [
            # [(departure_time, arrival_time, aircraft.id, flightplan.id)],
            [
                (datetime(2021, 4, 26, 0, 0, tzinfo=timezone.utc).time(),
                 datetime(2021, 4, 26, 6, 0, tzinfo=timezone.utc).time(), 1, 1),
                (datetime(2021, 4, 27, 0, 0, tzinfo=timezone.utc).time(),
                 datetime(2021, 4, 27, 6, 0, tzinfo=timezone.utc).time(), 1, 2),
                (datetime(2021, 4, 28, 0, 0, tzinfo=timezone.utc).time(),
                 datetime(2021, 4, 28, 6, 0, tzinfo=timezone.utc).time(), 1, 1),
                (datetime(2021, 4, 29, 0, 0, tzinfo=timezone.utc).time(),
                 datetime(2021, 4, 29, 6, 0, tzinfo=timezone.utc).time(), 1, 2),
                (datetime(2021, 4, 30, 0, 0, tzinfo=timezone.utc).time(),
                 datetime(2021, 4, 30, 6, 0, tzinfo=timezone.utc).time(), 1, 1),
                (datetime(2021, 5, 1, 0, 0, tzinfo=timezone.utc).time(),
                 datetime(2021, 5, 1, 6, 0, tzinfo=timezone.utc).time(), 1, 2),
                (datetime(2021, 5, 3, 0, 0, tzinfo=timezone.utc).time(),
                 datetime(2021, 5, 3, 6, 0, tzinfo=timezone.utc).time(), 1, 1)
            ],
        ]
        start_date, schedule = assign_employees(
            (start_date, schedule_variants))

        ans = [(*tup, [1, 2, 3]) for tup in schedule_variants[0]]
        self.assertEquals(start_date, start_date)
        self.assertEquals(ans, schedule)
