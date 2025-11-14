# /rentals/forms.py
from django import forms
from .models import Property, Application, MaintenanceTicket, Payment

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ["title", "address", "monthly_rent", "bedrooms", "bathrooms", "sqft", "description"]


# No PropertyImageForm needed!
# We handle images through request.FILES.getlist("images")


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["message"]


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTicket
        fields = ["title", "description", "status"]


class PaymentMarkPaidForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["method"]
