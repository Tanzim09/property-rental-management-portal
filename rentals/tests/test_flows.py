import pytest
from datetime import date
from django.urls import reverse
from django.contrib.auth.models import User
from rentals.models import Property, Application, Lease, Payment


@pytest.mark.django_db
def test_application_to_lease_flow(client):
    landlord = User.objects.create_user("l", password="x")
    landlord.profile.role = "LANDLORD"
    landlord.profile.save()

    tenant = User.objects.create_user("t", password="x")
    tenant.profile.role = "TENANT"
    tenant.profile.save()

    prop = Property.objects.create(
        title="A",
        address="X",
        monthly_rent=1200,
        bedrooms=2,
        bathrooms=1,
        sqft=500,
        landlord=landlord
    )

    # tenant applies
    client.login(username="t", password="x")
    url = reverse("rentals:apply", args=[prop.pk])
    client.post(url, {"message": "hello"})

    app = Application.objects.first()
    assert app is not None
    assert app.status == "PENDING"

    # landlord approves
    client.logout()
    client.login(username="l", password="x")

    appr_url = reverse("rentals:application_approve", args=[app.pk])
    client.get(appr_url)

    lease = Lease.objects.get(application=app)
    assert lease.tenant == tenant
    assert lease.rental_property == prop

    # payments created
    assert Payment.objects.filter(lease=lease).count() > 0
