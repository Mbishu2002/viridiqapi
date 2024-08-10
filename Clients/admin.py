from django.contrib import admin
from .models import Client, HealthData, DataRequest, CreditCard

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'profile_image')
    filter_horizontal = ('insurance_companies',)  

@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = ('client', 'timestamp')

@admin.register(DataRequest)
class DataRequestAdmin(admin.ModelAdmin):
    list_display = ('company', 'client', 'status', 'request_date')

@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ('client', 'last4', 'exp_month', 'exp_year')
