import json, os, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from model_mommy import mommy
from rest_framework.test import APIRequestFactory, force_authenticate
from .models import Company, Truck, Cargo, Shipment
from .views import Company, Truck, Cargo, Shipment, CompanyDetail, CompanyList

User = get_user_model()
factory = APIRequestFactory()

def read_json_fixture(fixture_name):
    content = ''
    with open(os.path.join('core', 'fixtures', fixture_name), 'r', encoding='utf-8') as f:
        content += f.read()
    return json.loads(content)

def post_request(url, data, user, view):
    request = factory.post(url, data, format='json')
    force_authenticate(request, user=user)
    return view(request)

def get_request(url, user, view, **kwargs):
    request = factory.get(url)
    if user:
        force_authenticate(request, user=user)
    return view(request, {}, **kwargs)

def delete_request(url, user, view, **kwargs):
    request = factory.delete(url)
    if user:
        force_authenticate(request, user=user)
    return view(request, {}, **kwargs)

class CompanyTestCase(TestCase):
    def setUp(self):
        self.user = mommy.make(User)
        self.company_list_view = CompanyList.as_view()
        self.company_detail_view = CompanyDetail.as_view()

    # Test that company can be created
    def test_create_company(self):
        company_obj = mommy.make(Company)
        response = post_request('api/company', company_obj, self.user, self.company_list_view)
        self.assertEqual(response.status_code, 201)

    # Test that company can be updated
    def test_update_company(self):
        company_obj = Company.objects.create(name="testcomp", description="testcompdesc", sign_up_datetime=datetime.datetime.now())
        company_obj.description = "testcompdescupdate"
        response = post_request('api/company', company_obj, self.user, self.company_list_view)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(company_obj.description, "testcompdescupdate")

    # Test that company can't be retrieved without permission
    def test_get_company(self):
        company_obj = mommy.make(Company)
        self.user2 = mommy.make(User)
        response = get_request(f'api/company/{company_obj.pk}', self.user2, self.company_detail_view)
        self.assertEqual(response.status_code, 403)

    # Test that company can't be deleted without permission
    def test_delete_company(self):
        company_obj = mommy.make(Company)
        response = delete_request(f'api/company/{company_obj.pk}', self.user, self.company_detail_view)
        self.assertEqual(response.status_code, 404)
