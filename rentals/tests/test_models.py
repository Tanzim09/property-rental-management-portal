import pytest
from datetime import date, timedelta
from rentals.models import Payment, Lease, Application, Property, generate_payment_schedule
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_payment_overdue_logic():
    user = User.objects.create(username="t")
    prop = Property.objects.create(
        title="A",
        address="X",
        monthly_rent=1000,
        bedrooms=2,
        bathrooms=1,
        sqft=500,
        landlord=user
    )

    app = Application.objects.create(
        rental_property=prop,
        tenant=user,
        message="test"
    )

    lease = Lease.objects.create(
        application=app,
        tenant=user,
        rental_property=prop,
        start_date=date.today(),
        end_date=date.today(),
        monthly_rent=1000,
        security_deposit=1000
    )

    payment = Payment.objects.create(
        lease=lease,
        due_date=date.today() - timedelta(days=10),
        amount=1000,
        status="DUE"
    )

    payment.apply_overdue_logic()
    payment.refresh_from_db()

    assert payment.status == "OVERDUE"
    assert payment.amount > 1000  # late fee applied


@pytest.mark.django_db
def test_generate_payment_schedule_creates_correct_number():
    user = User.objects.create(username="z")
    prop = Property.objects.create(
        title="A",
        address="X",
        monthly_rent=1000,
        bedrooms=2,
        bathrooms=1,
        sqft=500,
        landlord=user
    )

    app = Application.objects.create(
        rental_property=prop,
        tenant=user,
        message="test"
    )

    lease = Lease.objects.create(
        application=app,
        tenant=user,
        rental_property=prop,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 1),
        monthly_rent=500,
        security_deposit=500
    )

    generate_payment_schedule(lease)

    assert lease.payments.count() == lease.months
