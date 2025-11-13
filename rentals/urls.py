# /rentals/urls.py
from django.urls import path
from . import views

app_name = "rentals"

urlpatterns = [
    
    path("", views.listings, name="listings"),
    path("property/<int:pk>/", views.property_detail, name="property_detail"),
    path("property/new/", views.property_create, name="property_create"),
    path("property/<int:pk>/edit/", views.property_update, name="property_update"),
    path("property/<int:pk>/delete/", views.property_delete, name="property_delete"),

    
    path("property/<int:pk>/apply/", views.apply_for_property, name="apply"),
    path("applications/", views.applications_inbox, name="applications"),
    path("application/<int:pk>/approve/", views.application_approve, name="application_approve"),
    path("application/<int:pk>/reject/", views.application_reject, name="application_reject"),

    
    path("leases/", views.lease_dashboard, name="lease_dashboard"),
    path("payments/", views.payment_list, name="payments"),
    path("payment/<int:pk>/mark-paid/", views.payment_mark_paid, name="payment_mark_paid"),

   
    path("tickets/", views.maintenance_list, name="maintenance_list"),
    path("tickets/new/<int:lease_id>/", views.maintenance_create, name="maintenance_create"),
    path("ticket/<int:pk>/edit/", views.maintenance_update, name="maintenance_update"),

    
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
]
