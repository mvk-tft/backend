from django.contrib.auth import get_user_model
from django.test import TestCase
from model_mommy import mommy
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIRequestFactory, APIClient

from api.models import Company, Truck
from api.serializers import CompanySerializer, TruckSerializer

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

        company.description = 'test update'
        company_json = to_json_data(company, CompanySerializer)
        response = put_request(f'/api/company/{company.pk}/', company_json, self.primary_user)
        self.assertEqual(response.status_code, 200)

        updated_company = Company.objects.get(pk=company.pk)
        self.assertEqual(updated_company.description, 'test update')

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

    # Test that 1000 companies can be created
    def test_create_1000_companies(self):
        num_comp = 1000
        for i in range(num_comp):
            company = to_json_data(mommy.prepare(Company, name=f'company{i}'), CompanySerializer)
            response = post_request('/api/company/', company, self.primary_user)
            self.assertEqual(response.status_code, 201)

        companies = Company.objects.all()
        self.assertEqual(len(companies), num_comp)

        for i, company in enumerate(companies):
            self.assertEqual(company.name, f'company{i}')


class TruckTestCase(TestCase):
    def setUp(self):
        self.primary_user = mommy.make(User, is_staff=False)
        self.second_user = mommy.make(User, is_staff=False)
        self.admin_user = mommy.make(User, is_staff=True)

        self.primary_company = mommy.make(Company)
        self.primary_user.company = self.primary_company
        self.primary_user.save()

    # Create a truck and assign it to a company with primary_user as owner
    def create_truck(self, **kwargs):
        truck = mommy.make(Truck, **kwargs)
        truck.company = self.primary_company
        truck.save()
        return truck

    # Test that a Truck can be created
    def test_create_truck(self):
        truck = to_json_data(mommy.prepare(Truck, company=self.primary_company), TruckSerializer)
        response = post_request('/api/truck/', truck, self.primary_user)
        self.assertEqual(response.status_code, 201)

    # Test that 1000+ trucks can be created
    def test_create_1000_trucks(self):
        amount = 1500
        for i in range(amount):
            truck = to_json_data(mommy.prepare(Truck, company=self.primary_company, weight_capacity=i), TruckSerializer)
            response = post_request('/api/truck/', truck, self.primary_user)
            self.assertEqual(response.status_code, 201)

        trucks = Truck.objects.all()
        self.assertEqual(len(trucks), amount)

        for i, t in enumerate(trucks):
            self.assertEqual(t.weight_capacity, i)

    # Test that a truck can be deleted by a owner
    def test_delete_truck_as_owner(self):
        truck = self.create_truck()
        response = delete_request(f'/api/truck/{truck.pk}/', self.primary_user)
        self.assertEqual(response.status_code, 204)

    # Test that a truck can not be deleted by a user that isn't a owner
    def test_delete_truck_as_non_owner(self):
        truck = self.create_truck()
        response = delete_request(f'/api/truck/{truck.pk}/', self.second_user)
        self.assertEqual(response.status_code, 404)

    # Test that a truck can be updated by a owner
    def test_update_truck_as_owner(self):
        truck = self.create_truck()
        truck.weight_capacity = 100
        truck_json = to_json_data(truck, TruckSerializer)

        response = put_request(f'/api/truck/{truck.pk}/', truck_json, self.primary_user)
        self.assertEqual(response.status_code, 200)

        updated_truck = Truck.objects.get(pk=truck.pk)
        self.assertEqual(updated_truck.weight_capacity, 100)

    # Test that a truck can not be updated by a user that isn't a owner
    def test_update_truck_as_non_owner(self):
        truck = self.create_truck()
        previous_truck_weight_capacity = truck.weight_capacity
        truck.weight_capacity = 100
        truck_json = to_json_data(truck, TruckSerializer)

        response = put_request(f'/api/truck/{truck.pk}/', truck_json, self.second_user)
        self.assertEqual(response.status_code, 404)

        updated_truck = Truck.objects.get(pk=truck.pk)
        self.assertEqual(updated_truck.weight_capacity, previous_truck_weight_capacity)

    # Test that a truck can be retrieved by a owner
    def test_get_truck_as_owner(self):
        truck = self.create_truck()
        response = get_request(f'/api/truck/{truck.pk}/', self.primary_user)
        self.assertEqual(response.status_code, 200)

    # Test that a truck can not be retrieved by a non authorized user
    def test_get_truck_as_non_owner(self):
        truck = self.create_truck()
        response = get_request(f'/api/truck/{truck.pk}/', self.second_user)
        self.assertEqual(response.status_code, 404)

    # Test that a truck can be retrieved by admin user
    def test_get_truck_as_admin(self):
        truck = self.create_truck()
        response = get_request(f'/api/truck/{truck.pk}/', self.admin_user)
        self.assertEqual(response.status_code, 200)
