from django.contrib import admin
from .models import Profile, Property, Application, Lease, Payment, MaintenanceTicket


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "landlord", "monthly_rent", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "address", "landlord__username")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("rental_property", "tenant", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("rental_property__title", "tenant__username")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ("rental_property", "tenant", "start_date", "end_date", "monthly_rent", "is_active")
    inlines = [PaymentInline]


@admin.register(MaintenanceTicket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "lease", "title", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "lease__tenant__username")
