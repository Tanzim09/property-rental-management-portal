from django.urls import reverse, resolve
from rentals import views


def test_listings_resolves():
    assert resolve(reverse("rentals:listings")).func == views.listings


def test_application_reject_resolves():
    url = reverse("rentals:application_reject", args=[1])
    assert resolve(url).func == views.application_reject
