import datetime

import requests
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce

from api.models import Shipment


def split_shipments(shipments):
    # TODO: Split using a more fine-tuned parameter than cities
    #  e.g a custom map of addresses which are grouped together (time consuming to create, offers great control)
    #  or maybe postal codes or cities + another parameter
    nearby_shipments = {}
    for shipment in shipments:
        cities = (shipment.origin.city, shipment.destination.city)
        if cities in nearby_shipments.keys():
            nearby_shipments[cities].append(shipment)
        else:
            nearby_shipments[cities] = [shipment]
    return nearby_shipments


def get_time_estimations(driver: Shipment, other: Shipment, travel_time_sec, src_travel_time_sec, dst_travel_time_sec):
    expected_travel_time = datetime.timedelta(seconds=travel_time_sec)
    src_travel_time = datetime.timedelta(seconds=src_travel_time_sec)
    dst_travel_time = datetime.timedelta(seconds=dst_travel_time_sec)

    # Choose the earliest possible start time
    other_start_time = max(other.earliest_arrival_time - expected_travel_time, other.earliest_start_time)
    driver_start_time = max(other_start_time - src_travel_time, driver.earliest_start_time)

    other_start_time = driver_start_time + src_travel_time
    expected_other_arrival = other_start_time + expected_travel_time
    expected_driver_arrival = expected_other_arrival + dst_travel_time
    return driver_start_time, other_start_time, expected_other_arrival, expected_driver_arrival


def validate_times(driver: Shipment, other: Shipment, travel_time_sec, src_travel_time_sec, dst_travel_time_sec):
    src_travel_time = datetime.timedelta(seconds=src_travel_time_sec)
    if other.earliest_start_time > driver.latest_arrival_time + src_travel_time:
        return False
    if other.latest_start_time < driver.earliest_start_time + src_travel_time:
        return False

    # TODO: Include load-off time
    driver_st, other_st, expected_other_at, expected_driver_at = get_time_estimations(driver,
                                                                                      other,
                                                                                      travel_time_sec,
                                                                                      src_travel_time_sec,
                                                                                      dst_travel_time_sec)

    if driver.earliest_start_time > driver_st or driver.latest_start_time < driver_st:
        return False
    if driver.earliest_arrival_time > expected_driver_at or driver.latest_arrival_time < expected_driver_at:
        return False
    if other.earliest_start_time > other_st or other.latest_start_time < other_st:
        return False
    if other.earliest_arrival_time > expected_other_at or other.latest_arrival_time < expected_other_at:
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
    origins = list(map(lambda shipment: shipment.origin.address, shipments))
    destinations = list(map(lambda shipment: shipment.destination.address, shipments))

    # TODO: Optimize requests, restrict to 100 elements at most per request, 1000 per second.
    #  Not sustainable, use a another solution to calculate travel times
    src_src_time, src_dst_time, dst_dst_time = [], [], []
    for i in range(count):
        req_src, req_dst = [origins[i]], [destinations[i]]
        _, travel_time = request_distances_and_travel_times(req_src, req_dst)
        src_dst_time.append(travel_time[0][0])

        req_dst = origins[:i] + origins[i + 1:]
        _, travel_time = request_distances_and_travel_times(req_src, req_dst)
        src_src_time.append(travel_time[0])
        src_src_time[i].insert(i, 0)

        req_src, req_dst = [destinations[i]], destinations[:i] + destinations[i + 1:]
        _, travel_time = request_distances_and_travel_times(req_src, req_dst)
        dst_dst_time.append(travel_time[0])
        dst_dst_time[i].insert(i, 0)

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
                # TODO: Handle, possibly by simply removing from results
                raise RuntimeError(element['status'])
            distance[i].append(element['distance']['value'])
            travel_time[i].append(element['duration']['value'])
    return distance, travel_time
