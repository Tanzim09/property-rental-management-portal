from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from datetime import date

from .models import Property, Application, Lease, Payment, MaintenanceTicket, generate_payment_schedule, PropertyImage
from .forms import PropertyForm, ApplicationForm, MaintenanceForm, PaymentMarkPaidForm
from .decorators import role_required
from django.conf import settings
from django.urls import reverse


# Listings 
def listings(request):
    # All active properties and sorting by newest first.
    qs = Property.objects.filter(is_active=True).order_by("-created_at")
    return render(request, "listings.html", {"properties": qs})


def property_detail(request, pk):
    obj = get_object_or_404(Property, pk=pk)
    return render(request, "property_detail.html", {"property": obj})


@login_required
@role_required("LANDLORD", "ADMIN")
def property_create(request):
    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        files = request.FILES.getlist("images")  # multiple images if uploaded

        if form.is_valid():
            # Using commit=False so I can attach the landlord manually.
            p = form.save(commit=False)
            p.landlord = request.user
            p.save()

            # Looping through uploaded images.
            for f in files:
                PropertyImage.objects.create(property=p, image=f)

            messages.success(request, "Property created successfully.")
            return redirect("rentals:listings")

    else:
        form = PropertyForm()

    return render(request, "property_form.html", {"form": form, "mode": "Create"})


@login_required
@role_required("LANDLORD", "ADMIN")
def property_update(request, pk):
    p = get_object_or_404(Property, pk=pk, landlord=request.user)

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=p)
        files = request.FILES.getlist("images")  

        if form.is_valid():
            form.save()  

            # Append newly uploaded images.
            for f in files:
                PropertyImage.objects.create(property=p, image=f)

            messages.success(request, "Property updated.")
            return redirect("rentals:property_detail", pk=p.pk)

    else:
        form = PropertyForm(instance=p)

    return render(request, "property_form.html", {"form": form, "mode": "Edit"})


@login_required
@role_required("LANDLORD", "ADMIN")
def property_delete(request, pk):
    p = get_object_or_404(Property, pk=pk, landlord=request.user)
    p.delete()
    messages.info(request, "Property deleted.")
    return redirect("rentals:listings")


# Applications 
@login_required
def apply_for_property(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            # The form only holds the message.
            Application.objects.create(
                rental_property=prop,
                tenant=request.user,
                message=form.cleaned_data["message"],
            )
            messages.success(request, "Application submitted.")
            return redirect("rentals:listings")
    else:
        form = ApplicationForm()

    return render(request, "application_form.html", {"form": form, "property": prop})





@login_required
@role_required("LANDLORD", "ADMIN")
def applications_inbox(request):
    # Getting newest applications first.
    qs = (
        Application.objects
        .select_related("rental_property", "tenant")
        .order_by("-submitted_at")
    )

    # Non-staff landlords should only see their own properties' applications.
    if not request.user.is_staff:
        qs = qs.filter(rental_property__landlord=request.user)

    for app in qs:
        app.approve_url = reverse("rentals:application_approve", args=[app.pk])
        app.reject_url  = reverse("rentals:application_reject",  args=[app.pk])

    return render(request, "applications.html", {"applications": qs})


@login_required
@role_required("LANDLORD", "ADMIN")
@transaction.atomic  
def application_approve(request, pk):
    app = get_object_or_404(Application, pk=pk, status="PENDING")


    if not request.user.is_staff and app.rental_property.landlord != request.user:
        messages.error(request, "Not allowed.")
        return redirect("rentals:applications")

    # Marking app as approved before generating lease.
    app.status = "APPROVED"
    app.save()

    # Generating lease dates.
    months = int(getattr(settings, "DEFAULT_LEASE_MONTHS", 12))
    start = date.today()
    end_month = (start.month - 1 + (months - 1)) % 12 + 1  
    end_year = start.year + ((start.month - 1 + (months - 1)) // 12)
    end_day = min(start.day, 28)  # avoiding 30/31 overflow
    end = date(end_year, end_month, end_day)


    lease = Lease.objects.create(
        application=app,
        tenant=app.tenant,
        rental_property=app.rental_property,
        start_date=start,
        end_date=end,
        monthly_rent=app.rental_property.monthly_rent,
        security_deposit=app.rental_property.monthly_rent,  # using same as rent
        is_active=True,
    )

    # This generates all monthly payments.
    generate_payment_schedule(lease)

    messages.success(request, "Application approved and lease generated.")
    return redirect("rentals:applications")


@login_required
@role_required("LANDLORD", "ADMIN")
def application_reject(request, pk):

    app = get_object_or_404(Application, pk=pk, status="PENDING")

    if not request.user.is_staff and app.rental_property.landlord != request.user:
        messages.error(request, "Not allowed.")
        return redirect("rentals:applications")

    app.status = "REJECTED"
    app.save()

    messages.info(request, "Application rejected.")
    return redirect("rentals:applications")


# Lease & Payments
@login_required
def lease_dashboard(request):

    if request.user.is_staff:
        leases = Lease.objects.select_related("tenant", "rental_property").all()
    else:
        profile = request.user.profile  # roles stored here
        if profile.role == "LANDLORD":
            leases = Lease.objects.filter(rental_property__landlord=request.user)
        else:
            leases = Lease.objects.filter(tenant=request.user)

    return render(request, "lease_dashboard.html", {"leases": leases})


@login_required
def payment_list(request):
    
    for p in Payment.objects.all():
        p.apply_overdue_logic()

    
    if request.user.is_staff:
        qs = Payment.objects.select_related("lease", "lease__tenant", "lease__rental_property").all()
    else:
        profile = request.user.profile
        if profile.role == "LANDLORD":
            qs = Payment.objects.filter(lease__rental_property__landlord=request.user)
        else:
            qs = Payment.objects.filter(lease__tenant=request.user)

    return render(request, "payments.html", {"payments": qs})


@login_required
def payment_mark_paid(request, pk):
    
    payment = get_object_or_404(Payment, pk=pk)
    allowed = (
        request.user.is_staff
        or payment.lease.rental_property.landlord == request.user
        or payment.lease.tenant == request.user
    )

    if not allowed:
        messages.error(request, "Not allowed.")
        return redirect("rentals:payments")

    if request.method == "POST":
        form = PaymentMarkPaidForm(request.POST, instance=payment)
        if form.is_valid():
            
            pay = form.save(commit=False)
            pay.status = "PAID"
            pay.paid_on = date.today()
            pay.save()

            messages.success(request, "Payment recorded.")
            return redirect("rentals:payments")
    else:
        form = PaymentMarkPaidForm(instance=payment)

    return render(request, "payment_mark_paid.html", {"form": form, "payment": payment})


# Maintenance 
@login_required
def maintenance_list(request):
    
    if request.user.is_staff:
        qs = MaintenanceTicket.objects.select_related("lease", "lease__tenant", "lease__rental_property").all()
    else:
        profile = request.user.profile
        if profile.role == "LANDLORD":
            qs = MaintenanceTicket.objects.filter(lease__rental_property__landlord=request.user)
        else:
            qs = MaintenanceTicket.objects.filter(lease__tenant=request.user)

    return render(request, "maintenance_list.html", {"tickets": qs})


@login_required
def maintenance_create(request, lease_id):
    lease = get_object_or_404(Lease, pk=lease_id)

    # Only the involved tenant/landlord/staff can make tickets.
    allowed = (
        request.user.is_staff
        or lease.rental_property.landlord == request.user
        or lease.tenant == request.user
    )

    if not allowed:
        messages.error(request, "Not allowed.")
        return redirect("rentals:maintenance_list")

    if request.method == "POST":
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            # Assigning the lease + creator manually, since form doesn't have them.
            t = form.save(commit=False)
            t.lease = lease
            t.created_by = request.user
            t.save()

            messages.success(request, "Ticket created.")
            return redirect("rentals:maintenance_list")
    else:
        form = MaintenanceForm()

    return render(request, "maintenance_form.html", {"form": form, "lease": lease})


@login_required
@role_required("LANDLORD", "ADMIN")
def maintenance_update(request, pk):
    # Landlords can update tickets, but only for their properties.
    t = get_object_or_404(MaintenanceTicket, pk=pk)

    if not request.user.is_staff and t.lease.rental_property.landlord != request.user:
        messages.error(request, "Not allowed.")
        return redirect("rentals:maintenance_list")

    if request.method == "POST":
        form = MaintenanceForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            messages.success(request, "Ticket updated.")
            return redirect("rentals:maintenance_list")
    else:
        form = MaintenanceForm(instance=t)

    return render(request, "maintenance_form.html", {"form": form, "ticket": t})


# Admin Dashboard
@login_required
@role_required("LANDLORD", "ADMIN")
def admin_dashboard(request):

    total_props = Property.objects.count()
    pending_apps = Application.objects.filter(status="PENDING").count()
    active_leases = Lease.objects.filter(is_active=True).count()
    due_payments = Payment.objects.filter(status__in=["DUE", "OVERDUE"]).count()
    open_tickets = MaintenanceTicket.objects.filter(status__in=["OPEN", "IN_PROGRESS"]).count()

    context = {
        "total_props": total_props,
        "pending_apps": pending_apps,
        "active_leases": active_leases,
        "due_payments": due_payments,
        "open_tickets": open_tickets,
    }

    return render(request, "admin_dashboard.html", context)
