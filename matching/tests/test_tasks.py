import json
import os
import random
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from model_mommy import mommy

from api.models import Shipment, Location, Cargo, Truck
from matching.models import Match
from matching.task_helpers import request_distances_and_travel_times, split_shipments, validate_capacities, \
    validate_times, \
    calculate_travel_times
from matching.tasks import find_matches, matching_task


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
    src_src_time = [[0 if j == i else random.randint(1, 3200) for j in range(count)] for i in range(count)]
    dst_dst_time = [[0 if j == i else random.randint(1, 3200) for j in range(count)] for i in range(count)]
    src_dst_time = [random.randint(1, 5400) for _ in range(count)]
    return src_src_time, src_dst_time, dst_dst_time


class MatchingTestCase(TestCase):
    def setUp(self):
        # A - D
        # Start: 08:00 - 08:40 | Arrive: 10:00 - 10:30
        self.first = mommy.make(Shipment, origin=get_loc('A', city=''),
                                destination=get_loc('D', city=''),
                                truck=mommy.make(Truck, weight_capacity=50, volume_capacity=20),
                                earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                                latest_start_time=get_time(8, 40), latest_arrival_time=get_time(10, 30))
        # B - C
        # Start: 08:00 - 08:30 | Arrive: 10:00 - 10:30
        self.second = mommy.make(Shipment, origin=get_loc('B', city=''),
                                 destination=get_loc('C', city=''),
                                 earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                                 latest_start_time=get_time(8, 30), latest_arrival_time=get_time(10, 30))
        # X - Y
        # Start: 08:00 - 08:45 | Arrive: 10:00 - 10:15
        self.third = mommy.make(Shipment, origin=get_loc('X', city=''),
                                destination=get_loc('Y', city=''),
                                earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                                latest_start_time=get_time(8, 45), latest_arrival_time=get_time(10, 15))

        # First (outer) : Second (inner) -> A - B - C - D
        # 20 min + 30 min + 10 min -> Earliest start time: 09:00 (NOT OK)

        # First (outer) : Third (inner) -> A - X - Y - D
        # 40 min + 90 min + 10 min -> Earliest start time: 08:00 (OK)

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
        shipments = [mommy.prepare(Shipment, origin=mommy.prepare(Location, city=f'Src #{i % 5}'),
                                   destination=mommy.prepare(Location, city=f'Dst #{i % 5}')) for i in
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
        driver = mommy.make(Shipment, truck=truck, origin=mommy.make(Location, is_geocoded=True),
                            destination=mommy.make(Location, is_geocoded=True))
        other = mommy.make(Shipment, origin=mommy.make(Location, is_geocoded=True),
                           destination=mommy.make(Location, is_geocoded=True))
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
                               latest_start_time=get_time(9, 0), latest_arrival_time=get_time(10, 30))
        other = mommy.prepare(Shipment, earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                              latest_start_time=get_time(9, 0), latest_arrival_time=get_time(10, 30))

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

    @patch('matching.task_helpers.requests.get', autospec=True, side_effect=get_request_mock)
    def test_calculate_distances_and_travel_times(self, get_mock):
        shipments = Shipment.objects.all()
        src_src_time, src_dst_time, dst_dst_time = calculate_travel_times(shipments)

        self.assertEqual(get_mock.call_count, 9)
        self.assertListEqual(src_src_time, [
            [0, 1200, 2400],
            [1200, 0, 2400],
            [2400, 2400, 0],
        ])
        self.assertListEqual(src_dst_time, [3600, 1800, 5400])
        self.assertListEqual(dst_dst_time, [
            [0, 600, 600],
            [600, 0, 400],
            [600, 400, 0],
        ])

    @patch('matching.task_helpers.requests.get', autospec=True, side_effect=get_request_mock)
    def test_find_match(self, mock):
        shipments = Shipment.objects.all()
        nearby_shipments = split_shipments(shipments)
        matches, _ = find_matches(nearby_shipments)

        self.assertEqual(mock.call_count, 9)
        self.assertListEqual(matches, [(self.first.pk, -self.third.pk)])

    @patch('matching.task_helpers.requests.get', autospec=True, side_effect=get_request_mock)
    def test_find_match_with_already_waiting_matches(self, mock):
        mommy.make(Match, outer_shipment=self.first, inner_shipment=self.third, status=Match.Status.DEFAULT)
        matching_task()
        matches = Match.objects.all()

        #  TODO: Confirm the actual match instances
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(len(matches), 1)

    @patch('matching.task_helpers.requests.get', autospec=True, side_effect=get_request_mock)
    def test_find_match_with_rejected_matches(self, mock):
        mommy.make(Match, outer_shipment=self.first, inner_shipment=self.third, status=Match.Status.REJECTED)
        matching_task()
        matches = Match.objects.all()

        #  TODO: Confirm the actual match instances
        self.assertEqual(mock.call_count, 9)
        self.assertEqual(len(matches), 1)

    @patch('matching.tasks.calculate_travel_times', side_effect=randomize_times)
    def test_find_match_load(self, mock_travel_times):
        for _ in range(800):
            src = mommy.make(Location, is_geocoded=True, city='')
            dst = mommy.make(Location, is_geocoded=True, city='')
            truck = mommy.make(Truck, weight_capacity=random.randint(10, 100),
                               volume_capacity=random.randint(5, 25))
            shipment = mommy.make(Shipment, origin=src, destination=dst, truck=truck,
                                  earliest_start_time=get_time(8, 0), earliest_arrival_time=get_time(10, 0),
                                  latest_start_time=get_time(8, 40), latest_arrival_time=get_time(10, 30))

            mommy.make(Cargo, shipment=shipment, weight=random.randint(5, 40), volume=random.randint(1, 10))
        matching_task()
        matches = Match.objects.all()

        self.assertTrue(mock_travel_times.called)
        self.assertGreater(len(matches), 1)

    @patch('matching.tasks.find_matches', side_effect=lambda shipments, rejected: ([], {}))
    def test_match_celery_task(self, find_match_mock):
        matching_task()
        find_match_mock.assert_called_once()
