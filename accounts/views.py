from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.contrib.auth import logout


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome {user.username}! You’re registered as {user.profile.role}.")
            # Redirect based on role
            if user.profile.role == "LANDLORD":
                return redirect("rentals:admin_dashboard")
            else:
                return redirect("rentals:listings")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


def logout_user(request):
    logout(request)
    return redirect("rentals:listings")
