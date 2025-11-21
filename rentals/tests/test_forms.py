from rentals.forms import PaymentMarkPaidForm, MaintenanceForm


def test_payment_mark_paid_form_valid():
    form = PaymentMarkPaidForm(data={"method": "CASH"})
    assert form.is_valid()


def test_maintenance_form_missing_title():
    form = MaintenanceForm(data={"description": "x", "status": "OPEN"})
    assert not form.is_valid()
