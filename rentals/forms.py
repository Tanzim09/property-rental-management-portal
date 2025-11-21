
from django import forms
from .models import Property, Application, MaintenanceTicket, Payment

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ["title", "address", "monthly_rent", "bedrooms", "bathrooms", "sqft", "description"]



class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["message"]


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTicket
        fields = ["title", "description", "status"]


class PaymentMarkPaidForm(forms.ModelForm):
    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOBILE_PAY', 'Mobile Payment (bKash, Nagad, etc.)'),
        ('CARD', 'Credit/Debit Card'),
        ('CHECK', 'Check'),
    ]

    method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
    )

    class Meta:
        model = Payment
        fields = ['method']