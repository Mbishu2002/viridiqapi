from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group, Permission

from Clients.models import MyUserManager

class InsuranceCompany(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name='insurance_company_groups',  # Unique name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='insurance_company_user_permissions',  # Unique name
        blank=True,
    )
    company_name = models.CharField(max_length=255, unique=True, blank=True, null=True) 
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True) 
    username = None
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  
    objects = MyUserManager()

    def __str__(self):
        return self.company_name if self.company_name else self.email

class InsurancePlan(models.Model):
    company = models.ForeignKey(InsuranceCompany, related_name='plans', on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=255)
    description = models.TextField()
    coverage_details = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plan_name} - {self.company.company_name or 'No Company'}"

class Subscription(models.Model):
    client = models.ForeignKey('Clients.Client', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(InsurancePlan, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)  
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active')

    def __str__(self):
        return f"{self.client.first_name} - {self.plan.plan_name} ({self.status})"

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after the start date.")

class Claim(models.Model):
    client = models.ForeignKey('Clients.Client', related_name='claims', on_delete=models.CASCADE)
    plan = models.ForeignKey('InsurancePlan', related_name='claims', on_delete=models.CASCADE)
    description = models.TextField(null=True)
    amount_claimed = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')])
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Claim {self.id} by {self.client}"

class ClaimDocument(models.Model):
    claim = models.ForeignKey(Claim, related_name='documents', on_delete=models.CASCADE)
    document = models.FileField(upload_to='claims/documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def document_url(self):
        if self.document:
            return self.document.url
        return None

    def __str__(self):
        return f"Document {self.id} for Claim {self.claim.id}"
