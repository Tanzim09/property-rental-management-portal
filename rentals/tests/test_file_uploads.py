import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth.models import User
from rentals.models import Property, PropertyImage


@pytest.mark.django_db
def test_property_file_upload(client):
    landlord = User.objects.create_user("l", password="x")
    landlord.profile.role = "LANDLORD"
    landlord.profile.save()

    client.login(username="l", password="x")

    image = SimpleUploadedFile("test.jpg", b"filecontent", content_type="image/jpeg")

    url = reverse("rentals:property_create")

    resp = client.post(url, {
        "title": "House",
        "address": "X",
        "monthly_rent": 1000,
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 900,
        "description": "Nice",
        "images": image, 
    })

    assert resp.status_code == 302

    prop = Property.objects.first()
    assert PropertyImage.objects.filter(property=prop).exists()
