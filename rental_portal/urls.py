# /rental_portal/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="rentals:listings", permanent=False)),
    path("rentals/", include("rentals.urls")),
    path("accounts/", include("accounts.urls")),

    path("", include("django_prometheus.urls")),
]


