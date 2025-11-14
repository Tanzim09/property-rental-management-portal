from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, timedelta
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.contrib.auth.models import User


ROLE_CHOICES = (
    ("LANDLORD", "Landlord"),
    ("TENANT", "Tenant"),
)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.role})"



from django.db import models
from django.contrib.auth.models import User


class Property(models.Model):
    title = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    sqft = models.IntegerField()
    description = models.TextField(blank=True)
    landlord = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def first_image(self):
        img = self.images.first()
        return img.image.url if img else None

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="property_images/")

    def __str__(self):
        return f"Image of {self.property.title}"




APPLICATION_STATUS = (
    ("PENDING", "Pending"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
)

class Application(models.Model):
    rental_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="applications")
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    message = models.TextField()
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default="PENDING")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.username} -> {self.rental_property.title} ({self.status})"



class Lease(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="lease")
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leases")
    rental_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="leases")
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lease: {self.rental_property.title} - {self.tenant.username}"

    @property
    def months(self):
        return (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month) + 1



PAYMENT_STATUS = (
    ("DUE", "Due"),
    ("PAID", "Paid"),
    ("OVERDUE", "Overdue"),
)

class Payment(models.Model):
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="payments")
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="DUE")
    paid_on = models.DateField(null=True, blank=True)
    method = models.CharField(max_length=50, blank=True)
    late_fee_applied = models.BooleanField(default=False)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"Payment {self.due_date} - {self.amount} ({self.status})"

    def apply_overdue_logic(self):
        today = date.today()
        if self.status == "DUE":
            grace = timedelta(days=int(getattr(settings, "PAYMENT_GRACE_DAYS", 5)))
            if today > (self.due_date + grace):
                self.status = "OVERDUE"
                if not self.late_fee_applied:
                    percent = int(getattr(settings, "LATE_FEE_PERCENT", 5))
                    self.amount = self.amount + (self.amount * percent / 100)
                    self.late_fee_applied = True
                self.save()



MAINT_STATUS = (
    ("OPEN", "Open"),
    ("IN_PROGRESS", "In Progress"),
    ("RESOLVED", "Resolved"),
)

class MaintenanceTicket(models.Model):
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="tickets")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=MAINT_STATUS, default="OPEN")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket #{self.pk} - {self.title} ({self.status})"



@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, role="TENANT")



@transaction.atomic
def generate_payment_schedule(lease: Lease):
    start = lease.start_date
    for i in range(lease.months):
        month = (start.month - 1 + i) % 12 + 1
        year = start.year + ((start.month - 1 + i) // 12)
        day = min(start.day, 28)
        due = date(year, month, day)
        Payment.objects.create(
            lease=lease,
            due_date=due,
            amount=lease.monthly_rent,
            status="DUE",
        )
