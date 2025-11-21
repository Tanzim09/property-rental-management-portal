import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rentals.models import Property


@pytest.mark.django_db
def test_landlord_can_access_property_create(client):
    user = User.objects.create_user("ll", password="x")
    user.profile.role = "LANDLORD"
    user.profile.save()

    client.login(username="ll", password="x")

    resp = client.get(reverse("rentals:property_create"))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_tenant_cannot_access_property_create(client):
    user = User.objects.create_user("t", password="x")
    user.profile.role = "TENANT"
    user.profile.save()

    client.login(username="t", password="x")

    resp = client.get(reverse("rentals:property_create"))
    assert resp.status_code == 403  # PermissionDenied thrown
