import networkx as nx
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger
from django.db.models import Sum

from api.models import Shipment

logger = get_task_logger(__name__)


@periodic_task(run_every=(crontab(minute='*/1')), name='matching_task', ignore_result=True)
def test():
    shipments = Shipment.objects.select_related('starting_location', 'destination_location').prefetch_related(
        'cargo_set')
    nearby_shipments = {}
    for shipment in shipments:
        cities = (shipment.starting_location.city, shipment.destination_location.city)
        if cities in nearby_shipments.keys():
            nearby_shipments[cities].append(shipment)
        else:
            nearby_shipments[cities] = [shipment]

    def validate_times(driver: Shipment, other: Shipment, src_travel_time, dst_travel_time):
        # TODO: Implement
        return True

    def validate_capacities(driver: Shipment, other: Shipment):
        if driver.truck is None:
            return False
        if driver.cargo_set.aggregate(Sum('weight')) + other.cargo_set.aggregate(
                Sum('weight')) > driver.truck.weight_capacity:
            return False
        if driver.cargo_set.aggregate(Sum('volume')) + other.cargo_set.aggregate(
                Sum('volume')) > driver.truck.volume_capacity:
            return False
        return True

    graph = nx.Graph()
    for key, value in nearby_shipments.items():
        # TODO: Calculate distance, retrieve cached calculations
        starting_point_distance = [[1 for _ in range(len(value))] for _ in range(len(value))]
        max_distance = max(*(*starting_point_distance,))

        # TODO: Improve
        for f in value:
            if not f.truck:
                continue
            for s in value:
                if f.pk == s.pk:
                    continue
                if validate_times(f, s, 0, 0) and validate_capacities(f, s):
                    distance = starting_point_distance[f.pk][s.pk]
                    graph.add_edge(f.pk, s.pk, weight=max_distance - distance)
    results = nx.max_weight_matching(graph)
    # TODO: Save results
    print(results)
