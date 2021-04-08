from datetime import datetime

from celery import shared_task

from .models import Flight, FlightPlan, Runway, Aircraft

from django.utils import timezone
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True)
def check_airports_availability(self, flight_plan_pk):
    logger.info("Airports are currently being checked for availability")
    plan = FlightPlan.objects.get(pk=flight_plan_pk)
    plan.status = 1
    plan.save()
    source = Runway.objects.filter(airport=plan.source, is_active=True)
    destination = Runway.objects.filter(airport=plan.destination, is_active=True)
    stats = f"Source runways: {source.count()}, Destination runways: {destination.count()}"
    logger.info(stats)
    if not (source.count() and destination.count()):
        plan.status = 2
        plan.description = f"No available runways. {stats}"
        plan.save()
        self.request.chain = None
    return flight_plan_pk


def get_flights_datetimes(plan):
    logger.info(f"Start date: {plan.start_date}. End date: {plan.end_date}. Days: {plan.days_of_week}")
    current_date = plan.start_date
    results = []
    while current_date <= plan.end_date:
        if str(current_date.weekday()) in list(plan.days_of_week):
            departure_dt = datetime.combine(current_date, plan.planning_departure_time, tzinfo=timezone.utc)
            arrival_dt = datetime.combine(current_date, plan.planning_arrival_time, tzinfo=timezone.utc)
            if arrival_dt < departure_dt:
                arrival_dt += timezone.timedelta(days=1)
            results.append((departure_dt, arrival_dt))
        current_date += timezone.timedelta(days=1)
    return results


@shared_task
def generate_schedules(flight_plan_pk):
    logger.info(f"Generating schedules for {flight_plan_pk}")
    plan = FlightPlan.objects.get(pk=flight_plan_pk)
    aircrafts = Aircraft.objects.all()
    results = []
    for arrival_dt, departure_dt in get_flights_datetimes(plan):
        results.append((arrival_dt, departure_dt, aircrafts[0].pk))
    plan.status = 3
    plan.save()
    return flight_plan_pk, results


@shared_task
def assign_employees(data):
    flight_plan_pk, schedule = data[0], data[1]
    plan = FlightPlan.objects.get(pk=flight_plan_pk)
    plan.status = 4
    plan.save()
    # assign employee
    logger.info(f"Schedule: {schedule}")
    return flight_plan_pk, schedule, list([] for _ in schedule)


@shared_task
def create_flights(data):
    flight_plan_pk, schedule, employees = data[0], data[1], data[2]
    logger.info(f"Schedule: {schedule} Employees: {employees}")
    plan = FlightPlan.objects.get(pk=flight_plan_pk)
    for flight_info, employee in zip(schedule, employees):
        aircraft = Aircraft.objects.get(pk=flight_info[2])
        flight = Flight.objects.create(planning_arrival_datetime=flight_info[0],
                                       planning_departure_datetime=flight_info[1],
                                       aircraft=aircraft, has_arrived=False, flight_plan=plan)
        flight.save()
        logger.info(f"Flight info: {flight_info}.")
    plan.status = 6
    plan.save()
