from django.contrib import admin
from .models import InsuranceCompany, InsurancePlan, Subscription, Claim

@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'phone_number', 'location')
    search_fields = ('company_name', 'email')
    list_filter = ('location',)

@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'company', 'price', 'created_at')
    search_fields = ('plan_name', 'company__company_name')
    list_filter = ('company', 'price')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('client', 'plan', 'start_date', 'end_date', 'status')
    search_fields = ('client__name', 'plan__name')
    list_filter = ('status',)

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('client', 'plan', 'amount_claimed', 'status', 'date_submitted')
    search_fields = ('client__name', 'plan__name')
    list_filter = ('status',)
