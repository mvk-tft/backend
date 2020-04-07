import time
from unittest.mock import patch

from django.test import TestCase

from api.models import Location
from api.tasks import request_geocoding, geocode_location


class TasksTest(TestCase):
    @patch('api.models.tasks.geocode_location.delay', autospec=True)
    def test_geocode_task(self, mock_task):
        location = Location.objects.create(address='1600 Amphitheatre Parkway, Mountain View, CA', city='',
                                           postal_code='')
        # Assert that the task was called
        mock_task.assert_called_once_with(location.pk)
        geocode_location(location.pk)
        time.sleep(0.5)

        # Assert the final database instance
        location = Location.objects.get(pk=location.pk)
        self.assertAlmostEqual(location.latitude, 37.4224764, places=3)
        self.assertAlmostEqual(location.longitude, -122.0842499, places=3)
        self.assertTrue(location.is_geocoded)

    def test_geocode_manual(self):
        address = '1600 Amphitheatre Parkway, Mountain View, CA'
        lat, lng, formatted_address, postal_code, place_id = request_geocoding(address)
        self.assertAlmostEqual(lat, 37.4224764, places=3)
        self.assertAlmostEqual(lng, -122.0842499, places=3)
        self.assertEqual(postal_code, '94043')
