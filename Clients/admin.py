from django.contrib import admin
from .models import Client, HealthData, DataRequest, CreditCard, CustomToken, RiskProfile

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('email', 'profile_image', 'otp', 'otp_expires_at')
    search_fields = ('email',)
    list_filter = ['insurance_companies']
    ordering = ('email',)

@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = ('client', 'timestamp')
    search_fields = ('client__email',)
    ordering = ('-timestamp',)

@admin.register(DataRequest)
class DataRequestAdmin(admin.ModelAdmin):
    list_display = ('client', 'insurance_company', 'status', 'timestamp')
    search_fields = ('client__email', 'insurance_company__company_name')
    list_filter = ['status', 'insurance_company']
    ordering = ('-timestamp',)

@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ('client', 'last4', 'exp_month', 'exp_year')
    search_fields = ('client__email',)
    ordering = ('client',)

@admin.register(CustomToken)
class CustomTokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'client', 'insurance_company', 'created')
    search_fields = ('key', 'client__email', 'insurance_company__company_name')
    ordering = ('-created',)

@admin.register(RiskProfile)
class RiskProfileAdmin(admin.ModelAdmin):
    list_display = ('client', 'risk_level', 'last_updated')
    search_fields = ('client__email',)
    ordering = ('-last_updated',)
