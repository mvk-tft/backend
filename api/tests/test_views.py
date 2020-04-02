from django.contrib.auth import get_user_model
from django.test import TestCase
from model_mommy import mommy
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIRequestFactory, APIClient

from api.models import Company
from api.serializers import CompanySerializer

User = get_user_model()
factory = APIRequestFactory()
client = APIClient()
json_renderer = JSONRenderer()


def to_json_data(instance, serializer):
    return serializer(instance).data


# Used to create one item
def post_request(url, data, user):
    client.force_authenticate(user)
    return client.post(url, data, format='json')


# Used to update one item
def put_request(url, data, user):
    client.force_authenticate(user)
    return client.put(url, data, format='json')


# Used to get one or many items
def get_request(url, user, **kwargs):
    client.force_authenticate(user)
    return client.get(url, format='json', **kwargs)


# Used to delete one item
def delete_request(url, user, **kwargs):
    client.force_authenticate(user)
    return client.delete(url, format='json', **kwargs)


class CompanyTestCase(TestCase):
    def setUp(self):
        self.primary_user = mommy.make(User, is_staff=False)
        self.second_user = mommy.make(User, is_staff=False)
        self.admin_user = mommy.make(User, is_staff=True)

    # Create a company and assign the current user as the owner
    def create_company_and_set_owner(self, **kwargs):
        company = mommy.make(Company, **kwargs)
        self.primary_user.company = company
        self.primary_user.save()
        return company

    # Test that company can be created
    def test_create_company(self):
        company = to_json_data(mommy.prepare(Company), CompanySerializer)
        response = post_request('/api/company/', company, self.primary_user)
        self.assertEqual(response.status_code, 201)

    # Test that company can be updated
    def test_update_company_as_owner(self):
        company = self.create_company_and_set_owner()

        company.description = "test update"
        company_json = to_json_data(company, CompanySerializer)
        response = put_request(f'/api/company/{company.pk}/', company_json, self.primary_user)
        self.assertEqual(response.status_code, 200)

        updated_company = Company.objects.get(pk=company.pk)
        self.assertEqual(updated_company.description, "test update")

    # Test that company can be retrieved
    def test_get_company_as_owner(self):
        company = self.create_company_and_set_owner()

        response = get_request(f'/api/company/{company.pk}/', self.primary_user)
        self.assertEqual(response.status_code, 200)

    # Test that a company cannot be found or retrieved when the user is not the owner of the company
    def test_get_company_as_non_staff_user(self):
        company = self.create_company_and_set_owner()

        response = get_request(f'/api/company/{company.pk}/', self.second_user)
        self.assertEqual(response.status_code, 404)

    def test_get_company_as_admin(self):
        company = self.create_company_and_set_owner()

        response = get_request(f'/api/company/{company.pk}/', self.admin_user)
        self.assertEqual(response.status_code, 200)
