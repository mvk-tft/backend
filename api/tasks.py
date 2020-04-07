import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

import api.models as models

logger = get_task_logger(__name__)


@shared_task(bind=True)
def geocode_location(self, location_pk):
    loc = models.Location.objects.get(pk=location_pk)
    try:
        lat, lng, formatted_address, postal_code, place_id = request_geocoding(loc.address, loc.city)
    except ValueError:
        return
    except RuntimeError as exc:
        raise self.retry(exc=exc)
    if loc.postal_code and loc.postal_code != postal_code:
        raise RuntimeWarning('Postal code from Google Geocode API differs from user entered postal code')
    else:
        loc.postal_code = postal_code
    loc.latitude = lat
    loc.longitude = lng
    loc.address = formatted_address
    loc.place_id = place_id
    loc.is_geocoded = True
    loc.last_geocoding_update = timezone.now()
    loc.save()


def request_geocoding(*address):
    api_key = settings.GOOGLE_API_KEY
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    response = requests.get(f'{base_url}', params={'address': ','.join(address), 'language': 'sv', 'key': api_key})

    data = response.json()
    if data['status'] != 'OK':
        if data['status'] == 'ZERO_RESULTS':
            logger.log('Invalid address provided to geocoder')
            raise ValueError('Invalid address provided to geocoder')
        raise RuntimeError(data['status'])
    location = data['results'][0]['geometry']['location']
    formatted_address = data['results'][0]['formatted_address']
    place_id = data['results'][0].get('place_id')
    postal_code = next(
        item['long_name'] for item in data['results'][0]['address_components'] if 'postal_code' in item['types'])
    return location['lat'], location['lng'], formatted_address, postal_code, place_id
