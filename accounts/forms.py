from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from rentals.models import Profile

ROLE_CHOICES = (
    ("TENANT", "Tenant"),
    ("LANDLORD", "Landlord"),
)

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Register as")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "role"]

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data.get("role")
        if commit:
            profile = user.profile
            profile.role = role
            profile.save()
        return user
