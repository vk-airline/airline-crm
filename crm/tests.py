import os
from datetime import datetime, timezone
from django.test import TestCase, Client
from unittest.mock import patch
from .models import Employee, Airport, FlightPlan, Flight, Aircraft, AircraftDeviceLife
from .tasks import assign_employees
from django.utils import timezone
from django.utils.timezone import make_aware


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
        "crm.EmployeeLog.json",
    ]

    def test_planned_location_at(self):
        empl = Employee.objects.get(id=4)
        date = datetime.fromisoformat("2021-04-27T06:00:00+00:00")
        loc = empl.planned_location_at(date)
        self.assertEquals(loc, Airport.objects.get(id=1))

        date2 = datetime.fromisoformat("2021-04-25T06:00:00+00:00")
        loc2 = empl.planned_location_at(date2)
        self.assertFalse(loc2.exists())

    def test_is_available(self):
        john = Employee.objects.get(id=12)
        start = datetime.fromisoformat("2021-05-11T00:00:00+00:00")
        end = datetime.fromisoformat("2021-05-13T00:00:00+00:00")
        with self.subTest():
            self.assertTrue(john.is_available(start, end))

        start2 = end
        end2 = datetime.fromisoformat("2021-05-14T00:00:00+00:00")
        with self.subTest():
            self.assertFalse(john.is_available(start2, end2))

        start3 = start
        end3 = datetime.fromisoformat("2021-05-13T12:00:00+00:00")
        with self.subTest():
            self.assertFalse(john.is_available(start3, end3))

        start4 = datetime.fromisoformat("2021-05-18T12:00:00+00:00")
        end4 = datetime.fromisoformat("2021-05-19T12:00:00+00:00")
        with self.subTest():
            self.assertFalse(john.is_available(start4, end4))

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
                (datetime(2021, 4, 26, 0, 0, tzinfo=timezone.utc),
                 datetime(2021, 4, 26, 6, 0, tzinfo=timezone.utc), 1, 1),
                (datetime(2021, 4, 27, 0, 0, tzinfo=timezone.utc),
                 datetime(2021, 4, 27, 6, 0, tzinfo=timezone.utc), 1, 2),
                (datetime(2021, 4, 28, 0, 0, tzinfo=timezone.utc),
                 datetime(2021, 4, 28, 6, 0, tzinfo=timezone.utc), 1, 1),
                (datetime(2021, 4, 29, 0, 0, tzinfo=timezone.utc),
                 datetime(2021, 4, 29, 6, 0, tzinfo=timezone.utc), 1, 2),
                (datetime(2021, 4, 30, 0, 0, tzinfo=timezone.utc),
                 datetime(2021, 4, 30, 6, 0, tzinfo=timezone.utc), 1, 1),
                (datetime(2021, 5, 1, 0, 0, tzinfo=timezone.utc),
                 datetime(2021, 5, 1, 6, 0, tzinfo=timezone.utc), 1, 2),
                (datetime(2021, 5, 3, 0, 0, tzinfo=timezone.utc),
                 datetime(2021, 5, 3, 6, 0, tzinfo=timezone.utc), 1, 1)
            ],
        ]
        start_date, schedule = assign_employees(
            (start_date, schedule_variants))

        ans = [(*tup, [4, 5, 22, 23, 24, 25, 26, 27])
               for tup in schedule_variants[0]]
        self.assertEquals(start_date, start_date)
        self.assertEquals(ans, schedule)


class AircraftDeviceLifeTest(TestCase):
    fixtures = [
        "crm.Aircraft.json",
        "crm.AircraftDeviceLife.json",
    ]

    @patch('crm.models.datetime')
    def test_depart_update(self, mock):
        mock.now.return_value = datetime.now()
        device = AircraftDeviceLife.objects.get(pk=1)
        device.depart_update()
        self.assertEquals(device.total_operation_cycles, 2)
        self.assertEquals(device.after_service_cycles, 2)
        self.assertEquals(device.latest_update,
                          make_aware(mock.now.return_value))

    @patch('crm.models.datetime')
    def test_land_update(self, mock):
        mock.now.return_value = datetime.now()
        device = AircraftDeviceLife.objects.get(pk=1)
        device.land_update(12)
        self.assertEquals(device.total_operation_time_h, 13)
        self.assertEquals(device.after_service_time_h, 13)
        self.assertEquals(device.latest_update,
                          make_aware(mock.now.return_value))


class AircraftLifeTest(TestCase):
    fixtures = [
        "crm.Aircraft.json",
        "crm.AircraftDeviceLife.json",
    ]

    @patch('crm.models.datetime')
    def test_departed(self, mock):
        mock.now.return_value = datetime.now()
        aircraft = Aircraft.objects.get(pk=1)
        aircraft.departed()

        device = AircraftDeviceLife.objects.get(pk=1)
        self.assertEquals(device.total_operation_cycles, 2)
        self.assertEquals(device.after_service_cycles, 2)
        self.assertEquals(device.latest_update,
                          make_aware(mock.now.return_value))

    @patch('crm.models.datetime')
    def test_landed(self, mock):
        mock.now.return_value = datetime.now()
        aircraft = Aircraft.objects.get(pk=1)
        aircraft.landed(12)

        device = AircraftDeviceLife.objects.get(pk=1)
        self.assertEquals(device.total_operation_time_h, 13)
        self.assertEquals(device.after_service_time_h, 13)
        self.assertEquals(device.latest_update,
                          make_aware(mock.now.return_value))


class TestFlightPlanPage(TestCase):
    fixtures = [
        "auth.Group.json",
        "auth.User.json",
        "crm.Aircraft.json",
        "crm.Airport.json",
        "crm.FlightPlan.json",
    ]

    def setUp(self):
        self.client = Client()
        self.client.login(username=os.environ.get('ADMIN_LOGIN'), password=os.environ.get('ADMIN_PASSWORD'))

    def test_flight_plans_content(self):
        response = self.client.get('/crm/flightplans', follow=True)
        with self.subTest(msg='Request successful'):
            self.assertEquals(response.status_code, 200)
        print(response.render)
        required_elements = ['<nav class="navbar', '>Add new flight plan', 'LED-SVO</a>',
                             'Plan code', 'Source', 'Destination', 'Planning departure', 'Planning arrival',
                             'Passenger capacity', 'Start date', 'End date', 'Days of week', 'Status', 'Delete']
        for elem in required_elements:
            with self.subTest(msg=f"Elem {elem} on page"):
                self.assertContains(response, elem)

    def test_correct_hrefs(self):
        response = self.client.get('/crm/flightplans', follow=True)
        with self.subTest(msg='Request successful'):
            self.assertEquals(response.status_code, 200)
        curr_pos = 0
        while curr_pos != -1:
            pre_id_part = b'<a href="/crm/flightplans/'
            pre_name_part = b'">'
            plan_start = response.content.find(pre_id_part, curr_pos)
            if plan_start != -1:
                with self.subTest('Testing that flight plan has correct href'):
                    plan_id_end = response.content.find(pre_name_part, plan_start)
                    plan_id = int(response.content[plan_start + len(pre_id_part): plan_id_end])
                    plan_name_end = response.content.find(b'</a>', plan_id_end)
                    plan_name = response.content[plan_id_end + len(pre_name_part): plan_name_end]
                    self.assertEquals(FlightPlan.objects.get(pk=plan_id).flight_code, plan_name.decode('utf-8'))
                    curr_pos = plan_name_end
            else:
                break

    def test_flight_plan_delete_button(self):
        response = self.client.get('/crm/flightplans', follow=True)
        with self.subTest(msg='FlightPlan request successful'):
            self.assertEquals(response.status_code, 200)
        btn_href_start = b'onclick="window.location.href=\''
        btn_href_start_pos = response.content.find(btn_href_start)
        btn_href_end_pos = response.content.find(b'\'">', btn_href_start_pos)
        btn_href = response.content[btn_href_start_pos + len(btn_href_start): btn_href_end_pos].decode('utf-8')
        with self.subTest(msg='Test delete button has correct href'):
            self.assertEquals(btn_href, '/crm/flightplans/1/delete/')
        response = self.client.get('/crm/flightplans/1/delete/', follow=True)
        with self.subTest(msg='Delete Flight Plan form success'):
            self.assertEquals(response.status_code, 200)
        with self.subTest(msg='Has delete button'):
            self.assertContains(response, 'Delete flight plan LED-SVO')
        with self.subTest(msg='Delete button working'):
            with self.subTest(msg='Flight plan with pk=1 in db'):
                self.assertIsNotNone(FlightPlan.objects.get(pk=1))
            with self.subTest(msg='Delete post request success'):
                response = self.client.post('/crm/flightplans/1/delete/')
                self.assertEquals(response.status_code, 302)
            with self.assertRaises(FlightPlan.DoesNotExist):
                FlightPlan.objects.get(pk=1)

    def test_add_flight_plan_btn_working(self):
        response = self.client.get('/crm/flightplans', follow=True)
        with self.subTest(msg='FlightPlan request successful'):
            self.assertEquals(response.status_code, 200)
        btn_href_start = b'btn-success p-3"\n                onclick="window.location.href=\''
        btn_href_start_pos = response.content.find(btn_href_start)
        btn_href_end_pos = response.content.find(b'\'">', btn_href_start_pos)
        btn_href = response.content[btn_href_start_pos + len(btn_href_start): btn_href_end_pos].decode('utf-8')
        with self.subTest(msg='Test add button has correct href'):
            self.assertEquals(btn_href, '/crm/flightplans/add')


class TestFlightPlanAddForm(TestCase):
    fixtures = [
        "auth.Group.json",
        "auth.User.json",
        "crm.Aircraft.json",
        "crm.Airport.json",
        "crm.FlightPlan.json",
    ]

    def setUp(self):
        self.client = Client()
        self.client.login(username=os.environ.get('ADMIN_LOGIN'), password=os.environ.get('ADMIN_PASSWORD'))

    def test_correct_time_fields(self):
        not_correct_times = ['123', '25:00:32', '23:60:00', '24:00', '12:00a']
        for test_data in not_correct_times:
            with self.subTest(msg=f'Testing time field validation has error with value {test_data}'):
                response = self.client.post('/crm/flightplans/add', data={'planning_departure_time': test_data,
                                                                          'planning_arrival_time': test_data})
                self.assertContains(response, 'Enter a valid time.')
        test_data = '12:00:00'
        with self.subTest(msg=f'Testing time field validation no error with value {test_data}'):
            response = self.client.post('/crm/flightplans/add', data={'planning_departure_time': test_data,
                                                                      'planning_arrival_time': test_data})
            self.assertNotContains(response, 'Enter a valid time.')

    def test_correct_date_fields(self):
        not_correct_times = ['06-01-2021', '2021-13-01', '2021.01.01', '2021-01-00', '2021-05-06a']
        for test_data in not_correct_times:
            with self.subTest(msg=f'Testing time field validation has error with value {test_data}'):
                response = self.client.post('/crm/flightplans/add', data={'start_date': test_data,
                                                                          'end_date': test_data})
                self.assertContains(response, 'Enter a valid date.')
        test_data = '2021-06-01'
        with self.subTest(msg=f'Testing time field validation no error with value {test_data}'):
            response = self.client.post('/crm/flightplans/add', data={'start_date': test_data,
                                                                      'end_date': test_data})
            self.assertNotContains(response, 'Enter a valid date.')

    def test_required_fields(self):
        with self.subTest(msg=f'Testing fields required'):
            response = self.client.post('/crm/flightplans/add', data={'planning_departure_time': '12:00',
                                                                      'planning_arrival_time': '15:00',
                                                                      'start_date': '2021-06-01',
                                                                      'end_date': '2021-07-01',
                                                                      'passanger_capacity': 0,
                                                                      'status': 0})
            self.assertContains(response, 'This field is required.')

    def test_passanger_capacity_field(self):
        not_correct_data = ['1.1', '0a', 'a0']
        data = {'planning_departure_time': '12:00',
                'planning_arrival_time': '15:00',
                'start_date': '2021-06-01',
                'end_date': '2021-07-01',
                'source': 1, 'destination': 2,
                'passanger_capacity': '',
                'days_of_week': 1, 'flight_code': 'test',
                'status': 0}
        for test_data in not_correct_data:
            with self.subTest(msg=f'Testing time field validation has error with value {test_data}'):
                data['passanger_capacity'] = test_data
                response = self.client.post('/crm/flightplans/add', data=data)
                self.assertContains(response, 'Enter a whole number.')

        data['passanger_capacity'] = -1
        with self.subTest(msg=f'Testing time field validation has error with value {data["passanger_capacity"]}'):
            response = self.client.post('/crm/flightplans/add', data=data)
            self.assertContains(response, 'Ensure this value is greater than or equal to 0.')


class TestFlightPage(TestCase):
    fixtures = [
        "auth.Group.json",
        "auth.User.json",
        "crm.Aircraft.json",
        "crm.Airport.json",
        "crm.FlightPlan.json",
        "crm.Flights.json",
        "crm.Employee.json",
        "crm.Occupation.json",
        "crm.ScheduleConfig.json"
    ]

    def setUp(self):
        self.client = Client()
        self.client.login(username=os.environ.get('ADMIN_LOGIN'), password=os.environ.get('ADMIN_PASSWORD'))
        flight = Flight(flight_plan=FlightPlan.objects.first(), planning_departure_datetime=timezone.now(),
                        planning_arrival_datetime=timezone.now(), aircraft=Aircraft.objects.first(), id=1337)
        flight.employees.add(Employee.objects.first())
        flight.save()

    def test_flight_plans_content(self):
        response = self.client.get('/crm/flights', follow=True)
        with self.subTest(msg='Request successful'):
            self.assertEquals(response.status_code, 200)
        required_elements = ['<nav class="navbar', 'ID', 'Flight plan', 'Aircraft', 'Source', 'Destination',
                             'Planning departure datetime', 'Planning arrival datetime', 'Actual departure datetime',
                             'Actual arrival datetime', 'Actual Destination', 'Warnings', 'Delete']
        for elem in required_elements:
            with self.subTest(msg=f"Elem {elem} on page"):
                self.assertContains(response, elem)

    def test_flight_correct_hrefs(self):
        response = self.client.get('/crm/flights', follow=True)
        with self.subTest(msg='Request successful'):
            self.assertEquals(response.status_code, 200)
        with self.subTest(msg='Flight table has correct href'):
            self.assertContains(response, 'tr onclick="window.location=\'/crm/flights/1337')

    def test_flight_delete_button(self):
        response = self.client.get('/crm/flights', follow=True)
        with self.subTest(msg='Flights request successful'):
            self.assertEquals(response.status_code, 200)
        btn_href_start = b'onclick="window.location.href=\''
        btn_href_start_pos = response.content.find(btn_href_start)
        btn_href_end_pos = response.content.find(b'\'">', btn_href_start_pos)
        btn_href = response.content[btn_href_start_pos + len(btn_href_start): btn_href_end_pos].decode('utf-8')
        with self.subTest(msg='Test delete button has correct href'):
            self.assertEquals(btn_href, '/crm/flights/1337/delete/')
        response = self.client.get('/crm/flights/1337/delete/', follow=True)
        with self.subTest(msg='Delete Flight form success'):
            self.assertEquals(response.status_code, 200)
        with self.subTest(msg='Has delete button'):
            self.assertContains(response, 'Delete flight 1337')
        with self.subTest(msg='Delete button working'):
            with self.subTest(msg='Flight with pk=1337 in db'):
                self.assertIsNotNone(Flight.objects.get(pk=1337))
            with self.subTest(msg='Delete post request success'):
                response = self.client.post('/crm/flights/1337/delete/')
                self.assertEquals(response.status_code, 302)
            with self.assertRaises(Flight.DoesNotExist):
                Flight.objects.get(pk=1337)


class TestFlightPlanEditForm(TestCase):
    fixtures = [
        "auth.Group.json",
        "auth.User.json",
        "crm.Aircraft.json",
        "crm.Airport.json",
        "crm.FlightPlan.json",
        "crm.Flights.json",
        "crm.Employee.json",
        "crm.Occupation.json",
        "crm.ScheduleConfig.json"
    ]

    def setUp(self):
        self.client = Client()
        self.client.login(username=os.environ.get('ADMIN_LOGIN'), password=os.environ.get('ADMIN_PASSWORD'))
        flight = Flight(flight_plan=FlightPlan.objects.first(), planning_departure_datetime=timezone.now(),
                        planning_arrival_datetime=timezone.now(), aircraft=Aircraft.objects.first(), id=1337)
        flight.employees.add(Employee.objects.first())
        flight.save()

    def test_correct_datetime_fields(self):
        test_data = '2099-01-01 00:0001'
        with self.subTest(msg=f'Testing time field validation has error with value {test_data}'):
            response = self.client.post('/crm/flights/1337', data={'planning_departure_datetime': test_data,
                                                                   'planning_arrival_datetime': test_data})
            self.assertContains(response, 'Enter a valid date/time.')
        test_data = '2099-01-01 00:00:01'
        with self.subTest(msg=f'Testing time field validation has error with value {test_data}'):
            response = self.client.post('/crm/flights/1337', data={'planning_departure_datetime': test_data,
                                                                   'planning_arrival_datetime': test_data})
            self.assertNotContains(response, 'Enter a valid date/time.')

    def test_flight_edit_form_required_fields(self):
        with self.subTest(msg=f'Testing fields required'):
            response = self.client.post('/crm/flightplans/add',
                                        data={'planning_departure_datetime': '2099-01-01 00:00:01',
                                              'planning_arrival_datetime': '2099-01-01 00:00:010'})
            self.assertContains(response, 'This field is required.')
