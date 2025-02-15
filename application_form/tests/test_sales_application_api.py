import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from application_form.models.application import Application
from application_form.tests.conftest import create_application_data
from application_form.tests.utils import assert_profile_match_data
from customer.models import Customer
from users.enums import Roles
from users.models import Profile
from users.tests.factories import ProfileFactory
from users.tests.utils import _create_token


@pytest.mark.django_db
def test_sales_application_post_without_permission(
    api_client, elastic_single_project_with_apartments
):
    profile = ProfileFactory()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {_create_token(profile)}")
    data = create_application_data(profile)
    response = api_client.post(
        reverse("application_form:sales-application-list"), data, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_sales_application_post(api_client, elastic_single_project_with_apartments):
    salesperson_profile = ProfileFactory()
    salesperson_group = Group.objects.get(name__iexact=Roles.SALESPERSON.name)
    salesperson_group.user_set.add(salesperson_profile.user)

    customer_profile = ProfileFactory()
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {_create_token(salesperson_profile)}"
    )
    data = create_application_data(customer_profile)
    data["profile"] = customer_profile.id
    data["ssn_suffix"] = "XXXXX"  # ssn suffix should not be validated
    data["additional_applicant"]["ssn_suffix"] = "XXXXX"
    response = api_client.post(
        reverse("application_form:sales-application-list"), data, format="json"
    )
    assert response.status_code == 201
    assert response.data == {"application_uuid": data["application_uuid"]}

    application = Application.objects.get(external_uuid=data["application_uuid"])
    assert str(application.customer.primary_profile.id) == customer_profile.id


@pytest.mark.django_db
def test_sales_application_post_check_customer(
    api_client, elastic_single_project_with_apartments
):
    salesperson_profile = ProfileFactory()
    salesperson_group = Group.objects.get(name__iexact=Roles.SALESPERSON.name)
    salesperson_group.user_set.add(salesperson_profile.user)

    customer_profile = ProfileFactory()
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {_create_token(salesperson_profile)}"
    )
    assert Profile.objects.count() == 2
    assert Customer.objects.count() == 0

    def post_application(data):
        response = api_client.post(
            reverse("application_form:sales-application-list"), data, format="json"
        )
        assert response.status_code == 201
        application = Application.objects.get(external_uuid=data["application_uuid"])
        assert str(application.customer.primary_profile.id) == data["profile"]
        return application

    # post an application with a single profile customer
    data = create_application_data(customer_profile, num_applicants=1)
    data["profile"] = customer_profile.id
    application = post_application(data)
    assert Profile.objects.count() == 2
    assert Customer.objects.count() == 1
    assert application.customer.secondary_profile is None

    # post an application with the same single profile customer
    data = create_application_data(customer_profile, num_applicants=1)
    data["profile"] = customer_profile.id
    application = post_application(data)
    assert Profile.objects.count() == 2
    assert Customer.objects.count() == 1
    assert application.customer.secondary_profile is None

    # post an application with a two profile customer
    data = create_application_data(customer_profile)
    data["profile"] = customer_profile.id
    application = post_application(data)
    assert Profile.objects.count() == 3
    assert Customer.objects.count() == 2
    assert_profile_match_data(
        application.customer.secondary_profile, data["additional_applicant"]
    )

    # post an application with the same two profile customer
    additional_applicant = data["additional_applicant"]
    data = create_application_data(customer_profile)
    data["profile"] = customer_profile.id
    data["additional_applicant"] = additional_applicant
    application = post_application(data)
    assert Profile.objects.count() == 3
    assert Customer.objects.count() == 2
    assert_profile_match_data(
        application.customer.secondary_profile, data["additional_applicant"]
    )

    # verify that a secondary profile is not matched if the primary does not match
    existing_secondary_profile = application.customer.secondary_profile
    another_profile = ProfileFactory()
    data = create_application_data(another_profile)
    data["profile"] = another_profile.id
    data["additional_applicant"] = additional_applicant
    application = post_application(data)
    assert Profile.objects.count() == 5
    assert Customer.objects.count() == 3
    assert_profile_match_data(
        application.customer.secondary_profile, data["additional_applicant"]
    )
    assert application.customer.secondary_profile != existing_secondary_profile

    # verify that another single profile customer is not matched
    data = create_application_data(another_profile, num_applicants=1)
    data["profile"] = another_profile.id
    application = post_application(data)
    assert Profile.objects.count() == 5
    assert Customer.objects.count() == 4
    assert application.customer.secondary_profile is None
