from django.contrib import admin
from .models import InsuranceCompany, InsurancePlan, Subscription, Claim, ClaimDocument

@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'phone_number', 'location', 'website')
    search_fields = ('company_name', 'email', 'phone_number', 'location')
    list_filter = ['location']
    ordering = ('company_name',)
    readonly_fields = ('date_joined', 'last_login')

@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'company', 'price')
    search_fields = ('plan_name', 'company__company_name', 'description')
    list_filter = ['company']
    ordering = ('plan_name',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('client', 'plan', 'start_date', 'end_date', 'status')
    search_fields = ('client__first_name', 'plan__plan_name', 'status')
    list_filter = ['status', 'start_date', 'end_date']
    ordering = ('start_date',)

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('client', 'plan', 'amount_claimed', 'status', 'date_submitted')
    search_fields = ('client__first_name', 'plan__plan_name', 'status', 'description')
    list_filter = ['status', 'date_submitted']
    ordering = ('-date_submitted',)

@admin.register(ClaimDocument)
class ClaimDocumentAdmin(admin.ModelAdmin):
    list_display = ('claim', 'uploaded_at')
    search_fields = ('claim__id',)
    list_filter = ['uploaded_at']
    ordering = ('-uploaded_at',)
