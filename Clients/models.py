from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from cryptography.fernet import Fernet
from django.conf import settings
from django.utils import timezone
import pyotp

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    
# Helper function for encryption
def get_cipher_suite():
    return Fernet(settings.ENCRYPTION_KEY.encode())

# Client model
class Client(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name='client_groups',  
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='client_user_permissions',  
        blank=True,
    )
    email = models.EmailField(unique=True)
    username = None
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    insurance_companies = models.ManyToManyField('Insurance.InsuranceCompany', related_name='clients', null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 
    objects = MyUserManager() 

    def generate_otp(self):
        totp = pyotp.TOTP('base32secret3232')  
        self.otp = totp.now()
        self.otp_expires_at = timezone.now() + timezone.timedelta(minutes=10)
        self.save()
        return self.otp

    def verify_otp(self, otp):
        totp = pyotp.TOTP('base32secret3232')  # Replace with your own key
        return totp.verify(otp) and self.otp_expires_at > timezone.now()

# HealthData model with encryption
class HealthData(models.Model):
    client = models.ForeignKey(Client, related_name='health_data', on_delete=models.CASCADE)
    data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        cipher_suite = get_cipher_suite()
        if isinstance(self.data, str):
            self.data = cipher_suite.encrypt(self.data.encode('utf-8')).decode('utf-8')
        super().save(*args, **kwargs)

    def get_data(self):
        cipher_suite = get_cipher_suite()
        return cipher_suite.decrypt(self.data.encode('utf-8')).decode('utf-8')

# DataRequest model
class DataRequest(models.Model):
    company = models.ForeignKey('Insurance.InsuranceCompany', related_name='data_requests', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, related_name='data_requests', on_delete=models.CASCADE)
    request_data = models.JSONField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')])
    request_date = models.DateTimeField(auto_now_add=True)

# CreditCard model with encryption
class CreditCard(models.Model):
    client = models.OneToOneField(Client, related_name='credit_card', on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    last4 = models.CharField(max_length=4)
    exp_month = models.PositiveIntegerField()
    exp_year = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        cipher_suite = get_cipher_suite()
        self.token = cipher_suite.encrypt(self.token.encode('utf-8')).decode('utf-8')
        super().save(*args, **kwargs)

    def get_token(self):
        cipher_suite = get_cipher_suite()
        return cipher_suite.decrypt(self.token.encode('utf-8')).decode('utf-8')
