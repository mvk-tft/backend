import json
import os
import random
from unittest.mock import patch

from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.test import TestCase
from django.utils import timezone
from model_mommy import mommy

from api.models import Shipment, Location, Cargo, Truck
from matching.tasks import request_distances_and_travel_times, split_shipments, validate_capacities, validate_times, \
    calculate_travel_times, find_matches, matching_task


def get_time(hour, minute):
    return timezone.now().replace(hour=hour, minute=minute, second=0, microsecond=0)


def get_loc(address, **kwargs):
    return mommy.make(Location, is_geocoded=True, address=address, **kwargs)


def read_json_fixture(fixture_name):
    content = ''
    with open(os.path.join('matching', 'fixtures', fixture_name), 'r', encoding='utf-8') as f:
        content += f.read()
    return json.loads(content)


def get_request_mock(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    origins = kwargs['params']['origins']
    destinations = kwargs['params']['destinations']
    if origins == 'A' and destinations == 'D':
        return MockResponse(read_json_fixture('distance_matrix_response_ad.json'), 200)
    elif origins == 'B' and destinations == 'C':
        return MockResponse(read_json_fixture('distance_matrix_response_bc.json'), 200)
    elif origins == 'X' and destinations == 'Y':
        return MockResponse(read_json_fixture('distance_matrix_response_xy.json'), 200)
    elif origins == 'A' and destinations == 'B|X':
        return MockResponse(read_json_fixture('distance_matrix_response_abx.json'), 200)
    elif origins == 'B' and destinations == 'A|X':
        return MockResponse(read_json_fixture('distance_matrix_response_bax.json'), 200)
    elif origins == 'X' and destinations == 'A|B':
        return MockResponse(read_json_fixture('distance_matrix_response_xab.json'), 200)
    elif origins == 'D' and destinations == 'C|Y':
        return MockResponse(read_json_fixture('distance_matrix_response_dcy.json'), 200)
    elif origins == 'C' and destinations == 'D|Y':
        return MockResponse(read_json_fixture('distance_matrix_response_cdy.json'), 200)
    elif origins == 'Y' and destinations == 'D|C':
        return MockResponse(read_json_fixture('distance_matrix_response_ydc.json'), 200)
    return MockResponse(None, 404)


def randomize_times(shipments):
    count = len(shipments)
    src_src_time = [[0 if j == i else random.randint(1, 3000) for j in range(count)] for i in range(count)]
    dst_dst_time = [[0 if j == i else random.randint(1, 3000) for j in range(count)] for i in range(count)]
    src_dst_time = [random.randint(1, 3000) for _ in range(count)]
    return src_src_time, src_dst_time, dst_dst_time


class MatchingTestCase(TestCase):
    def setUp(self):
        mommy.make(Shipment, starting_location=get_loc('A', city=''),
                   destination_location=get_loc('D', city=''),
                   truck=mommy.make(Truck, weight_capacity=50, volume_capacity=20),
                   earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                   latest_start_time=get_time(8, 40), latest_arrival_time=get_time(10, 30)),
        mommy.make(Shipment, starting_location=get_loc('B', city=''),
                   destination_location=get_loc('C', city=''),
                   earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                   latest_start_time=get_time(8, 30), latest_arrival_time=get_time(10, 30)),
        mommy.make(Shipment, starting_location=get_loc('X', city=''),
                   destination_location=get_loc('Y', city=''),
                   earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                   latest_start_time=get_time(8, 45), latest_arrival_time=get_time(10, 15)),

    def test_distance_and_travel_time(self):
        if settings.GOOGLE_API_KEY is None:
            return

        origins = ['Attundavägen 29', 'Förmansvägen 11']
        destinations = ['Friskis&Svettis Abrahamsberg, Registervägen 38, 168 31 Bromma',
                        'Friskis&Svettis, Skomakargatan 9, 781 70 Borlänge']
        distances, times = request_distances_and_travel_times(origins, destinations)

        self.assertGreater(distances[0][0], 3000)
        self.assertLess(distances[0][0], 4000)

        self.assertGreater(distances[0][1], 200000)
        self.assertLess(distances[0][1], 250000)

        self.assertGreater(distances[1][0], 9000)
        self.assertLess(distances[1][0], 10000)

        self.assertGreater(distances[1][1], 220000)
        self.assertLess(distances[1][1], 280000)

    def test_split_shipments(self):
        shipments = [mommy.prepare(Shipment, starting_location=mommy.prepare(Location, city=f'Src #{i % 5}'),
                                   destination_location=mommy.prepare(Location, city=f'Dst #{i % 5}')) for i in
                     range(10)]
        nearby_shipments = split_shipments(shipments)
        self.assertEqual(len(nearby_shipments.keys()), 5)
        self.assertIn(('Src #0', 'Dst #0'), nearby_shipments.keys())
        self.assertIn(('Src #1', 'Dst #1'), nearby_shipments.keys())
        self.assertIn(('Src #2', 'Dst #2'), nearby_shipments.keys())
        self.assertIn(('Src #3', 'Dst #3'), nearby_shipments.keys())
        self.assertIn(('Src #4', 'Dst #4'), nearby_shipments.keys())
        self.assertEqual(nearby_shipments[('Src #0', 'Dst #0')], [shipments[0], shipments[5]])
        self.assertEqual(nearby_shipments[('Src #1', 'Dst #1')], [shipments[1], shipments[6]])
        self.assertEqual(nearby_shipments[('Src #2', 'Dst #2')], [shipments[2], shipments[7]])
        self.assertEqual(nearby_shipments[('Src #3', 'Dst #3')], [shipments[3], shipments[8]])
        self.assertEqual(nearby_shipments[('Src #4', 'Dst #4')], [shipments[4], shipments[9]])

    def test_validate_capacities(self):
        truck = mommy.make(Truck, weight_capacity=50, volume_capacity=10)
        driver = mommy.make(Shipment, truck=truck, starting_location=mommy.make(Location, is_geocoded=True),
                            destination_location=mommy.make(Location, is_geocoded=True))
        other = mommy.make(Shipment, starting_location=mommy.make(Location, is_geocoded=True),
                           destination_location=mommy.make(Location, is_geocoded=True))
        driver_cargo = mommy.make(Cargo, shipment=driver, weight=5, volume=3)
        mommy.make(Cargo, shipment=other, weight=10, volume=2)
        mommy.make(Cargo, shipment=other, weight=30, volume=4)

        self.assertFalse(validate_capacities(other, driver))
        self.assertTrue(validate_capacities(driver, other))

        driver_cargo.volume = 5
        driver_cargo.save()
        self.assertFalse(validate_capacities(driver, other))

    def test_validate_times(self):
        driver = mommy.prepare(Shipment, earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                               latest_start_time=get_time(8, 30), latest_arrival_time=get_time(10, 30))
        other = mommy.prepare(Shipment, earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                              latest_start_time=get_time(8, 30), latest_arrival_time=get_time(10, 30))

        # Times in seconds
        src_travel_time = 1200  # Travel time between origins (A - B)
        expected_travel_time = 3600  # Time from origin of 'other' to destination (B - C)
        dst_travel_time = 60  # Travel time between destinations (C - D)

        # 20 minutes from A to B, 60 minutes from B to C, 1 minute from C to D.
        # Earliest possible start time for driver: 8:40 (10:00 - 1 hour - 20 minutes)
        self.assertTrue(validate_times(driver, other, expected_travel_time, src_travel_time, dst_travel_time))

        # 20 minutes C to D.
        self.assertTrue(validate_times(driver, other, expected_travel_time, src_travel_time, 20 * dst_travel_time))
        # 30 minutes C to D
        self.assertTrue(validate_times(driver, other, expected_travel_time, src_travel_time, 30 * dst_travel_time))
        # 31 minutes C to D
        self.assertFalse(validate_times(driver, other, expected_travel_time, src_travel_time, 31 * dst_travel_time))

        driver.earliest_start_time = get_time(9, 0)
        # Earliest possible start time for driver: 9:00, latest for other: 8:30
        self.assertFalse(validate_times(driver, other, expected_travel_time, src_travel_time, dst_travel_time))
        other.latest_start_time = get_time(9, 20)
        # 9:00 - 9:20 - 10:20 - 10:21
        self.assertTrue(validate_times(driver, other, expected_travel_time, src_travel_time, dst_travel_time))

    @patch('matching.tasks.requests.get', autospec=True, side_effect=get_request_mock)
    def test_calculate_distances_and_travel_times(self, get_mock):
        shipments = Shipment.objects.all()
        src_src_time, src_dst_time, dst_dst_time = calculate_travel_times(shipments)

        self.assertEqual(get_mock.call_count, 9)
        self.assertListEqual(src_src_time, [
            [0, 1200, 2200],
            [1200, 0, 2400],
            [2200, 2400, 0],
        ])
        self.assertListEqual(src_dst_time, [3600, 1800, 5400])
        self.assertListEqual(dst_dst_time, [
            [0, 600, 800],
            [600, 0, 400],
            [800, 400, 0],
        ])

    @patch('matching.tasks.requests.get', autospec=True, side_effect=get_request_mock)
    def test_find_match(self, mock):
        shipments = Shipment.objects.all()
        nearby_shipments = split_shipments(shipments)
        matches = find_matches(nearby_shipments, [])

        self.assertEqual(mock.call_count, 9)
        self.assertListEqual(matches, [(shipments[0].pk, shipments[1].pk)])

    @patch('matching.tasks.requests.get', autospec=True, side_effect=get_request_mock)
    def test_find_match_with_disallowed_matches(self, mock):
        shipments = Shipment.objects.all()
        nearby_shipments = split_shipments(shipments)
        matches = find_matches(nearby_shipments, [(2, 1)])  # (1, 2) and (2, 1) are considered the same

        self.assertEqual(mock.call_count, 9)
        self.assertListEqual(matches, [(shipments[0].pk, shipments[2].pk)])

    @patch('matching.tasks.calculate_travel_times', side_effect=randomize_times)
    def test_find_match_load(self, mock_travel_times):
        for _ in range(400):
            src = mommy.make(Location, is_geocoded=True, city='')
            dst = mommy.make(Location, is_geocoded=True, city='')
            if random.random() < 0.5:
                truck = mommy.make(Truck, weight_capacity=random.randint(10, 100),
                                   volume_capacity=random.randint(5, 25))
            else:
                truck = None
            shipment = mommy.make(Shipment, starting_location=src, destination_location=dst, truck=truck,
                                  earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                                  latest_start_time=get_time(8, 40), latest_arrival_time=get_time(10, 30))

            mommy.make(Cargo, shipment=shipment, weight=random.randint(5, 40), volume=random.randint(1, 10))
        shipments = Shipment.objects.annotate(cargo_weight=Coalesce(Sum('cargo__weight'), 0)).annotate(
            cargo_volume=Coalesce(Sum('cargo__volume'), 0))
        nearby_shipments = split_shipments(shipments)
        matches = find_matches(nearby_shipments, [])

        self.assertTrue(mock_travel_times.called)
        self.assertGreater(len(matches), 1)

    @patch('matching.tasks.find_matches', side_effect=lambda x, y: [])
    def test_match_celery_task(self, find_match_mock):
        matching_task()
        find_match_mock.assert_called_once()
