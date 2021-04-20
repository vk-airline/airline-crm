from datetime import datetime, timezone
from django.test import TestCase
from .models import Employee, Airport


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
        self.assertEquals(loc2, Airport.objects.none())

