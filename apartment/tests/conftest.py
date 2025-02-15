import faker.config
from django.conf import settings
from elasticsearch.helpers.test import get_test_client
from elasticsearch_dsl.connections import add_connection
from pytest import fixture
from rest_framework.test import APIClient

from apartment.tests.factories import ApartmentDocumentFactory

faker.config.DEFAULT_LOCALE = "fi_FI"


@fixture
def api_client():
    api_client = APIClient()
    return api_client


def setup_elasticsearch():
    test_client = get_test_client()
    add_connection("default", test_client)
    if test_client.indices.exists(index=settings.APARTMENT_INDEX_NAME):
        test_client.indices.delete(index=settings.APARTMENT_INDEX_NAME)
    test_client.indices.create(index=settings.APARTMENT_INDEX_NAME)
    return test_client


def teardown_elasticsearch(test_client):
    if test_client.indices.exists(index=settings.APARTMENT_INDEX_NAME):
        test_client.indices.delete(index=settings.APARTMENT_INDEX_NAME)


@fixture(scope="module")
def elasticsearch():
    test_client = setup_elasticsearch()
    yield test_client
    teardown_elasticsearch(test_client)


@fixture
def elastic_apartments(elasticsearch):
    apartments = ApartmentDocumentFactory.create_batch(10)
    yield apartments
    for apartment in apartments:
        apartment.delete(refresh=True)


@fixture
def elastic_project_with_5_apartments(elasticsearch):
    apartments = []

    apartment = ApartmentDocumentFactory()
    apartments.append(apartment)

    for _ in range(4):
        apartments.append(ApartmentDocumentFactory(project_uuid=apartment.project_uuid))
    yield apartment.project_uuid, apartments

    for apartment in apartments:
        apartment.delete(refresh=True)
