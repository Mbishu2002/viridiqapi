from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from cryptography.fernet import Fernet
from django.conf import settings
from django.utils import timezone
import json
import pyotp
import binascii
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Helper function for encryption
def get_cipher_suite():
    return Fernet(settings.ENCRYPTION_KEY.encode())

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
    otp = models.CharField(max_length=255, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 
    objects = MyUserManager() 

    def generate_otp(self):
        self.otp = pyotp.random_base32()
        totp = pyotp.TOTP(self.otp, interval=300)
        otp_code = totp.now()
        self.otp_expires_at = timezone.now() + timezone.timedelta(minutes=5)
        self.save()
        return otp_code

    def verify_otp(self, otp):
        totp = pyotp.TOTP(self.otp, interval=300)
        return totp.verify(otp)

    def update_risk_profile(self):
        now = timezone.now()
        start_time = now - timezone.timedelta(days=1)
        recent_health_data = self.health_data.filter(timestamp__gte=start_time)
        steps_data = [data.get_steps() for data in recent_health_data]

        if not steps_data:
            risk_profile, created = RiskProfile.objects.update_or_create(
                client=self,
                defaults={'risk_level': 'No Data'}
            )
        else:
            avg_steps = sum(steps_data) / len(steps_data)
            risk_level = assess_risk_level(avg_steps)
            risk_profile, created = RiskProfile.objects.update_or_create(
                client=self,
                defaults={'risk_level': risk_level}
            )

def assess_risk_level(steps):
    if steps < 5000:
        return 'High Risk'
    elif steps < 10000:
        return 'Moderate Risk'
    else:
        return 'Low Risk'

class HealthData(models.Model):
    client = models.ForeignKey(Client, related_name='health_data', on_delete=models.CASCADE)
    data = models.TextField()  
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        cipher_suite = get_cipher_suite()
        if isinstance(self.data, dict):  
            self.data = cipher_suite.encrypt(json.dumps(self.data).encode('utf-8')).decode('utf-8')
        else:
            logger.error("Data to encrypt is not a dictionary: %s", self.data)
        super().save(*args, **kwargs)
        self.client.update_risk_profile()

    def get_data(self):
        cipher_suite = get_cipher_suite()
        try:
            decrypted_data = cipher_suite.decrypt(self.data.encode('utf-8')).decode('utf-8')
            return json.loads(decrypted_data)
        except Exception as e:
            logger.error("Decryption error: %s", e)
            return {}

    def get_steps(self):
        data = self.get_data()
        return data.get('steps', 0)

class DataRequest(models.Model):
    client = models.ForeignKey(Client, related_name='data_requests', on_delete=models.CASCADE)
    insurance_company = models.ForeignKey('Insurance.InsuranceCompany', null=True, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'insurance_company')  


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
        try:
            return cipher_suite.decrypt(self.token.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error("Token decryption error: %s", e)
            return None

class CustomToken(models.Model):
    key = models.CharField(max_length=40, unique=True)
    client = models.ForeignKey('Client', null=True, blank=True, on_delete=models.CASCADE)
    insurance_company = models.ForeignKey('Insurance.InsuranceCompany', null=True, blank=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key

class RiskProfile(models.Model):
    client = models.OneToOneField(Client, related_name='risk_profile', on_delete=models.CASCADE)
    risk_level = models.CharField(max_length=20)
    last_updated = models.DateTimeField(auto_now=True)
