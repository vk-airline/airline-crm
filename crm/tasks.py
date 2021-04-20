import dataclasses
from collections import defaultdict
from datetime import datetime, time
from itertools import chain
from operator import itemgetter

from celery import shared_task
from django.db.models import Max, Q

from .models import Flight, FlightPlan, Runway, Aircraft, Airport, AircraftDynamicInfo, Employee

from django.utils import timezone
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True)
def check_airports_availability(self, flight_plan_pk):
    logger.info("Airports are currently being checked for availability")
    plan = FlightPlan.objects.get(pk=flight_plan_pk)
    plan.status = FlightPlan.PROCESSING_FPM
    plan.save()
    source = Runway.objects.filter(airport=plan.source, is_active=True)
    destination = Runway.objects.filter(airport=plan.destination, is_active=True)
    stats = f"Source runways: {source.count()}, Destination runways: {destination.count()}"
    logger.info(stats)
    if not (source.count() and destination.count()):
        plan.status = FlightPlan.ERROR_FPM
        plan.description = f"No available runways. {stats}"
        plan.save()
        self.request.chain = None
    return flight_plan_pk


def get_flights_datetimes(plan: FlightPlan, starts_datetime=None):
    logger.info(f"Start date: {plan.start_date}. End date: {plan.end_date}. Days: {plan.days_of_week}")
    current_date = plan.start_date
    if starts_datetime is not None and current_date <= starts_datetime.date():
        current_date = starts_datetime.date()
    results = []
    while current_date <= plan.end_date:
        if str(current_date.weekday()) in list(plan.days_of_week):
            departure_dt = datetime.combine(current_date, plan.planning_departure_time, tzinfo=timezone.now().tzinfo)
            arrival_dt = datetime.combine(current_date, plan.planning_arrival_time, tzinfo=timezone.now().tzinfo)
            if arrival_dt < departure_dt:
                arrival_dt += timezone.timedelta(days=1)
            if departure_dt >= starts_datetime:
                results.append((departure_dt, arrival_dt, plan.pk))
        current_date += timezone.timedelta(days=1)
    return results


class ScheduleError(Exception):
    pass


def get_actually_available_aircraft(airport: Airport):
    aircraft_flight = Flight.objects.filter(canceled=False, actual_destination=airport,
                                            actual_arrival_datetime__lte=timezone.now()).values(
        'aircraft').annotate(last_arrival=Max('actual_arrival_datetime'))
    logger.info(f"Flights: {aircraft_flight}")
    # TODO: optimise there:
    valid = filter(lambda flight: Flight.objects.filter(flight_plan__source=airport,
                                                        actual_departure_datetime__gte=flight[
                                                            'last_arrival']).count() == 0,
                   aircraft_flight)
    return map(lambda availability_info: availability_info['aircraft'], valid)


def get_planned_available_aircraft(airport: Airport, datetime_point: datetime):
    # TODO: make it smarter, this implementation guarantee that result is correct
    # current algo:
    # get all available aircraft now
    # apply all flights: arrived -> add, departure -> remove
    # return residual aircraft list

    # it might be a smarter algo, but a lot of transactions:
    #  get list of all aircraft
    #  look when every aircraft last arrived ('planned_arrived_datetime' field)
    #  check that aircraft not departure from airport in range [arrived, planned_arrived_datetime]

    all_aircraft = {aircraft for aircraft in get_actually_available_aircraft(airport)}
    logger.info(f"Now in airport {airport}: {all_aircraft}")
    flights = Flight.objects.filter(
        Q(flight_plan__destination=airport, planning_arrival_datetime__lt=datetime_point) |
        Q(flight_plan__source=airport, planning_departure_datetime__lt=datetime_point),
        canceled=False).order_by('planning_arrival_datetime')
    for flight in flights:
        if flight.flight_plan.source == airport and flight.flight_plan.destination != airport:
            if flight.aircraft.pk not in all_aircraft:
                raise ScheduleError(
                    f"Aircraft {flight.aircraft} not in airport {airport} at {flight.planning_departure_datetime}")
            logger.info(f"Aicraft {flight.aircraft.pk} removed: {flight}")
            all_aircraft.remove(flight.aircraft.pk)
        elif flight.flight_plan.destination == airport and flight.flight_plan.source != airport:
            if flight.aircraft in all_aircraft:
                raise ScheduleError(
                    f"Aircraft {flight.aircraft} is already in airport {airport} at {flight.planning_arrival_datetime}")
            all_aircraft.add(flight.aircraft.pk)
            logger.info(f"Aicraft {flight.aircraft.pk} added: {flight}")
        elif flight.flight_plan.source == airport and flight.flight_plan.destination == airport:
            pass
        else:
            raise RuntimeError(f"Wrong query, flight {flight} is not connected with {airport} airport")
    return all_aircraft


def aircraft_smart_chooser(departure: datetime, arrival: datetime, plan: FlightPlan, aircraft_list: set):
    for aircraft in aircraft_list:
        craft_info = AircraftDynamicInfo.objects.get(aircraft=aircraft)
        capacity = craft_info.business_class_cap + craft_info.first_class_cap + craft_info.economy_class_cap
        if capacity >= plan.passanger_capacity:
            return aircraft
    return None


@shared_task(bind=True)
def generate_schedules(self, start_dt: str):
    start_dt = timezone.datetime.fromisoformat(start_dt)
    logger.info(f"Generating schedules from {start_dt.date()}")
    plans = FlightPlan.objects.filter(end_date__gte=start_dt.date())
    plans.update(status=FlightPlan.PROCESSING_FPM)
    flights_info = list(chain.from_iterable(get_flights_datetimes(plan, starts_datetime=start_dt) for plan in plans))
    flights_info = sorted(flights_info, key=itemgetter(0))
    logger.info(f"Flights info: {flights_info}")
    banned_flights = Flight.objects.filter(canceled=True, planning_departure_datetime__gte=start_dt)
    banned_flights = set(map(lambda f: (f.planning_departure_datetime, f.planning_arrival_datetime, f.flight_plan.pk),
                             banned_flights))
    logger.info(f"Banned flights: {banned_flights}")
    schedule = []
    available_aircraft = defaultdict(set)
    in_flight = []
    for departure, arrival, plan_pk in flights_info:
        while in_flight and in_flight[0][0] <= departure:
            dep, destination, craft = in_flight.pop(0)
            available_aircraft[destination].add(craft)
            logger.info(f"Aicraft: {craft} arrived to {destination}")
        if (departure, arrival, plan_pk) not in banned_flights:
            plan = FlightPlan.objects.get(pk=plan_pk)
            if plan.source not in available_aircraft:
                available_aircraft[plan.source] = get_planned_available_aircraft(plan.source, departure)
            aircraft = aircraft_smart_chooser(departure, arrival, plan, available_aircraft[plan.source])
            if aircraft is None:
                logger.info(f"Available: {available_aircraft}")
                plan.description = f"Cannot create flight by plan {plan} with departure: {departure}. There is no " \
                                   f"available aircraft. All aircraft list: {available_aircraft[plan.source]}"
                plan.status = FlightPlan.ERROR_FPM
                plan.save()
                self.request.chain = None
                return  # DO NOT REMOVE THIS THERE IS NO ELSE CASE
            available_aircraft[plan.source].remove(aircraft)
            logger.info(f"Aircraft: {aircraft} departure from {plan.source}")
            in_flight.append((arrival, plan.destination, aircraft))
            schedule.append((departure, arrival, aircraft, plan.pk))
    return start_dt, [schedule]


@dataclasses.dataclass
class EmployeeState:  # Класс, энкапсулирующий состояние конкретного сотрудника на одной итерации алгоритма
    obj: Employee
    location: Airport
    time: datetime  # дата последнего изменения состояния


@shared_task(bind=True)
def assign_employees(self, data):
    start_dt, schedules = data
    states: list[EmployeeState] = [
        # if current location of an employee is unknown, we assume
        # he is in LED
        EmployeeState(emp, emp.planned_location_at(start_dt)
                      or Airport.objects.get(id=1), start_dt)
        for emp in Employee.objects.all().order_by('id')
    ]

    variants = []
    for flights in schedules:
        variant = []
        for (departure_time, arrival_time, aircraft_id, plan_id) in flights:
            aircraft = Aircraft.objects.get(id=aircraft_id)
            flight_plan = FlightPlan.objects.get(id=plan_id)

            # this can be a complex predicate that decides
            # whether or not an employee is suitable for the flight
            def predicate(employeeState):
                return (employeeState.location == flight_plan.source
                        and
                        employeeState.time <= departure_time)

            available = list(filter(predicate, states))
            adi = aircraft.aircraftdynamicinfo

            # IndexError implies failure to find
            try:
                # Occupation ID:
                # pilot = 1
                # second pilot = 2
                pilots = [e for e in available if e.obj.occupation.id in [
                    1, 2]][:adi.pilots_number]
                # senior attendant = 3
                # attendant = 4
                attendants = [e for e in available if e.obj.occupation.id in [
                    3, 4]][:adi.attendants_number]
            except IndexError:
                self.request.chain = None
                return

            crew = pilots + attendants

            for state in crew:
                state.location = flight_plan.destination
                state.time = arrival_time

            variant.append(
                (departure_time, arrival_time, aircraft_id,
                 plan_id, [p.obj.id for p in crew])
            )
        variants.append(variant)

    # TODO: evaluate each one of the possible variants of crew
    # configureations and choose the best one
    def choose_best(variants):
        return variants[0]

    return start_dt, choose_best(variants)


@shared_task
def create_flights(data):
    start_dt, schedule = data
    logger.info(f"Schedule: {schedule}")
    # TODO Make all queries in single transaction
    Flight.objects.filter(canceled=False, planning_departure_datetime__gte=start_dt).delete()
    for departure, arrival, aircraft, plan_pk, crew in schedule:
        plan = FlightPlan.objects.get(pk=plan_pk)
        aircraft = Aircraft.objects.get(pk=aircraft)
        logger.info(f"Departure: {departure} Arrival: {arrival} Aircraft: {aircraft} Plan:  {plan}")
        flight = Flight.objects.create(planning_departure_datetime=departure,
                                       planning_arrival_datetime=arrival,
                                       aircraft_id=aircraft,
                                       flight_plan_id=plan)
        flight.employees.set(crew)
        flight.save()
        plan.status = FlightPlan.SUCCESS  # HAHA
        plan.save()
