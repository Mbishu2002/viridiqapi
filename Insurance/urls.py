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
    manage_subscriptions
)

urlpatterns = [
    path('register/', register_insurance_company, name='register_insurance_company'),
    path('verify-email/<str:uidb64>/<str:token>/', verify_email, name='verify_email'),
    path('login/', login, name='login'),
    path('clients/', list_clients, name='list_clients'),
    path('plans/create/', create_insurance_plan, name='create_insurance_plan'),
    path('clients/<int:client_id>/', view_client_profile, name='view_client_profile'),
    path('claims/update-status/<int:subscription_id>/', update_claim_status, name='update_claim_status'),
    path('data-request/<int:client_id>/', request_client_data, name='request_client_data'),
    path('subscriptions/', manage_subscriptions, name='manage_subscriptions'),
]
