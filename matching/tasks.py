import datetime

import networkx as nx
import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce

from api.models import Shipment
from matching.models import Match, RejectedMatch

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def update_rejections_task():
    rejected_matches = Match.objects.filter(status=Match.Status.REJECTED)
    rejections = []

    for match in rejected_matches:
        rejections.append(RejectedMatch(outer_shipment_pk=match.outer_shipment.pk,
                                        inner_shipment_pk=match.inner_shipment.pk))
        match.delete()

    RejectedMatch.objects.bulk_create(rejections)

    logger.info(f'Rejections updated: {len(rejections)}')


@shared_task(ignore_result=True)
def matching_task():
    # Only retrieve shipments not yet matched
    shipments = Shipment.objects.filter(match_outer=None, match_inner=None).select_related('starting_location',
                                                                                           'destination_location') \
        .prefetch_related('cargo_set')
    disallowed_matches = list(map(lambda item: (item.outer_shipment_pk, item.inner_shipment_pk),
                                  RejectedMatch.objects.all()))
    matches = find_matches(split_shipments(shipments), disallowed_matches)
    prepared = []
    for (f, s) in matches:
        # Outer shipment is the one going the whole route and whose truck will be used
        match = Match(outer_shipment=shipments.get(pk=f), inner_shipment=shipments.get(pk=s))
        prepared.append(match)
    Match.objects.bulk_create(matches)


def split_shipments(shipments):
    nearby_shipments = {}
    for shipment in shipments:
        cities = (shipment.starting_location.city, shipment.destination_location.city)
        if cities in nearby_shipments.keys():
            nearby_shipments[cities].append(shipment)
        else:
            nearby_shipments[cities] = [shipment]
    return nearby_shipments


def find_matches(nearby_shipments, disallowed_matches):
    graph = nx.Graph()
    results = []
    for key, value in nearby_shipments.items():
        graph.clear()
        count = len(value)

        # Travel time between the two origins, last origin and first arrival and the two destinations, respectively
        src_src_time, src_dst_time, dst_dst_time = calculate_travel_times(value)
        max_time = max(map(max, src_src_time)) + max(src_dst_time) + max(map(max, dst_dst_time))

        for i in range(count):
            f = value[i]
            if not f.truck:
                continue
            for j in range(count):
                s = value[j]
                if i == j or (f.pk, s.pk) in disallowed_matches or (s.pk, f.pk) in disallowed_matches:
                    continue

                src_travel_time = src_src_time[i][j]
                dst_travel_time = dst_dst_time[i][j]
                travel_time = src_dst_time[j]

                if validate_times(f, s, travel_time, src_travel_time, dst_travel_time) and validate_capacities(f, s):
                    total_time = src_travel_time + travel_time + dst_travel_time
                    graph.add_edge(f.pk, s.pk, weight=max_time - total_time)
        results += list(nx.max_weight_matching(graph, maxcardinality=True))
    return results


def validate_times(driver: Shipment, other: Shipment, travel_time_sec, src_travel_time_sec, dst_travel_time_sec):
    expected_travel_time = datetime.timedelta(seconds=travel_time_sec)
    src_travel_time = datetime.timedelta(seconds=src_travel_time_sec)
    dst_travel_time = datetime.timedelta(seconds=dst_travel_time_sec)

    if other.earliest_start_time > driver.latest_arrival_time + src_travel_time:
        return False
    if other.latest_start_time < driver.earliest_start_time + src_travel_time:
        return False

    # Choose the earliest possible start time
    other_start_time = max(other.earliest_arrival_time - expected_travel_time, other.earliest_start_time)
    driver_start_time = max(other_start_time - src_travel_time, driver.earliest_start_time)
    expected_first_arrival = driver_start_time + src_travel_time + expected_travel_time

    # Possibly show warning
    # If the truck can't go from origin to destination within the time limit then the user's inputs may be too strict
    if other.earliest_arrival_time > expected_first_arrival or other.latest_arrival_time < expected_first_arrival:
        return False

    # TODO: Include load-off time
    if driver.earliest_arrival_time > expected_first_arrival + dst_travel_time:
        return False
    if driver.latest_arrival_time < expected_first_arrival + dst_travel_time:
        return False
    return True


def validate_capacities(driver: Shipment, other: Shipment):
    if driver.truck is None:
        return False

    def try_get_weight(shipment: Shipment):
        try:
            # noinspection PyUnresolvedReferences
            return shipment.cargo_weight
        except AttributeError:
            return shipment.cargo_set.aggregate(sum=Coalesce(Sum('weight'), 0))['sum']

    def try_get_volume(shipment: Shipment):
        try:
            # noinspection PyUnresolvedReferences
            return shipment.cargo_volume
        except AttributeError:
            return shipment.cargo_set.aggregate(sum=Coalesce(Sum('volume'), 0))['sum']

    driver_cargo_weight = try_get_weight(driver)
    other_cargo_weight = try_get_weight(other)
    if driver_cargo_weight + other_cargo_weight > driver.truck.weight_capacity:
        return False

    driver_cargo_volume = try_get_volume(driver)
    other_cargo_volume = try_get_volume(other)
    if driver_cargo_volume + other_cargo_volume > driver.truck.volume_capacity:
        return False

    return True


def calculate_travel_times(shipments: [Shipment]):
    count = len(shipments)
    origins = list(map(lambda shipment: shipment.starting_location.address, shipments))
    destinations = list(map(lambda shipment: shipment.destination_location.address, shipments))

    # TODO: Optimize requests, restrict to 100 elements at most per request, 1000 per second
    src_src_time, src_dst_time, dst_dst_time = [], [], []
    for i in range(count):
        _, travel_time = request_distances_and_travel_times([origins[i]], [destinations[i]])
        src_dst_time.append(travel_time[0][0])

        _, travel_time = request_distances_and_travel_times([origins[i]], origins[:i] + origins[i + 1:])
        src_src_time.append(travel_time[0])  # Only one origin
        src_src_time[i].insert(i, 0)

        _, travel_time = request_distances_and_travel_times([destinations[i]], destinations[:i] + destinations[i + 1:])
        dst_dst_time.append(travel_time[0])  # Only one origin
        dst_dst_time[i].insert(i, 0)

    # origins = [f'place_id:{origin.place_id}' if origin.place_id else origin.address for origin in origins]
    # destinations = [f'place_id:{dst.place_id}' if dst.place_id else dst.address for dst in destinations]
    #
    # distances, travel_times = {}, {}
    # for i in range(0, count, 10):
    #     origins_group = origins[i:i + 10]
    #     for j in range(0, count, 10):
    #         destinations_group = destinations[j:j + 10]
    #         distance, travel_time = request_distances_and_travel_times(origins_group, destinations_group)
    #         distances = {**distances, **distance}
    #         travel_times = {**travel_times, **travel_time}

    return src_src_time, src_dst_time, dst_dst_time


def request_distances_and_travel_times(origins, destinations):
    api_key = settings.GOOGLE_API_KEY
    base_url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    response = requests.get(f'{base_url}', params={
        'origins': '|'.join(origins),
        'destinations': '|'.join(destinations),
        'language': 'sv',  # We prefer Swedish names for now
        'key': api_key})

    data = response.json()
    if data['status'] != 'OK':
        raise RuntimeError(data['status'])
    distance = []
    travel_time = []

    rows = data['rows']
    for i, row in enumerate(rows):
        distance.append([])
        travel_time.append([])
        for j, element in enumerate(row['elements']):
            if element['status'] != 'OK':
                # TODO: Handle
                continue
            distance[i].append(element['distance']['value'])
            travel_time[i].append(element['duration']['value'])
    return distance, travel_time
