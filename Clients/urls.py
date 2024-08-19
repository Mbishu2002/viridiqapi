from django.urls import path
from . import views

urlpatterns = [
    # Registration and Authentication
    path('register/', views.register_client, name='register_client'),
    path('login/', views.login_with_token, name='login_with_token'),
    path('register-with-insurance/', views.register_with_insurance, name='register_with_insurance'),
    path('verify/', views.verify_otp, name="otp_verification"),
    path('resend-otp/', views.resend_otp, name='resend_otp'),

    # Forgot and Reset Password
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.password_reset_confirm, name='reset_password'),

    # Client Profile
    path('profile/', views.get_client_profile, name='get_client_profile'),
    path('profile/update', views.update_profile, name='update_profile'),

    # Health Data
    path('health-data/', views.get_health_data, name='get_health_data'),
    path('health-data/save/', views.save_health_data, name='save_health_data'),

    # Data Requests
    path('data-requests/', views.get_data_requests, name='get_data_requests'),
    path('data-requests/<int:request_id>/status/', views.update_data_request_status, name='update_data_request_status'),

    # Claims
    path('claims/', views.get_claims, name='get_claims'),
    path('claims/submit/', views.submit_claim, name='submit_claim'),

    # Insurance Plans
    path('insurance-plans/', views.get_insurance_plans, name='get_insurance_plans'),

    # Subscriptions
    path('subscribe/', views.subscribe_to_plan, name='subscribe_to_plan'),
    path('unsubscribe/', views.unsubscribe_from_plan, name='unsubcribe'),
    path('subscribed-plans/', views.get_subscribed_plans, name='client_subscribed_plans'),

    # Credit Card Details
    path('credit-card/', views.get_credit_cards, name='add_credit_card'),
    path('credit-card/add/', views.add_credit_card, name='add_credit_card'),
    path('credit-card/update/<int:card_id>/', views.update_credit_card, name='update_credit_card'),
    path('credit-card/delete/<int:card_id>/', views.delete_credit_card, name='delete_credit_card'),
]
