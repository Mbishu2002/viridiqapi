from django.urls import path
from .views import (
    register_insurance_company,
    verify_email,
    login,
    list_clients,
    create_insurance_plan,
    view_client_profile,
    update_claim_status,
    request_client_data,
    manage_subscriptions,
    email_confirmation,
    update_insurance_profile,
    get_claims_by_company,
    list_plans_with_subscribers,
    get_plan_by_id,
    get_client_profile
)

urlpatterns = [
    path('register/', register_insurance_company, name='register_insurance_company'),
    path('verify-email/<str:uidb64>/<str:token>/', email_confirmation, name='verify_email'),
    path('login/', login, name='login'),
    path('clients/', list_clients, name='list_clients'),
    path('plans/create/', create_insurance_plan, name='create_insurance_plan'),
    path('clients/<int:client_id>/', view_client_profile, name='view_client_profile'),
    path('claims/update-status/<int:subscription_id>/', update_claim_status, name='update_claim_status'),
    path('data-request/<int:client_id>/', request_client_data, name='request_client_data'),
    path('subscriptions/', manage_subscriptions, name='manage_subscriptions'),
    path('update-profile/', update_insurance_profile, name='update_insurance_profile'),
    path('claims/', get_claims_by_company, name='get_claims'),  
    path('plans/', list_plans_with_subscribers, name='list_plans_with_subscribers'),
    path('plan/<int:plan_id>/', get_plan_by_id, name='get_plan_by_id'),
    path('client-profile/<int:client_id>/', get_client_profile, name='get_client_profile'),
]
