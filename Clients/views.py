from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils.encoding import force_bytes, force_str
from django.core.files.storage import default_storage
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.tokens import default_token_generator
from rest_framework.authtoken.models import Token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
import pyotp
from .models import HealthData, DataRequest, CreditCard, Client
from .serializers import ClientSerializer, HealthDataSerializer, DataRequestSerializer, CreditCardSerializer
from Insurance.models import Claim, InsurancePlan, Subscription
from Insurance.serializers import ClaimSerializer, InsurancePlanSerializer, SubscriptionSerializer
from django.conf import settings
import datetime

# Registration views
@api_view(['POST'])
def register_client(request):
    serializer = ClientSerializer(data=request.data)
    if serializer.is_valid():
        password = request.data.get('password')
        if password:
            user = get_user_model()(**serializer.validated_data)
            user.password = make_password(password)
            user.save()
            otp = user.generate_otp() 
            # Send OTP to the user
            subject = 'Your OTP Code'
            message = render_to_string('otp_email.html', {
                'otp_code': otp,
                'current_year': datetime.datetime.now().year
                })
            email = EmailMessage(subject, message, settings.EMAIL_FROM, [user.email])  
            email.content_subtype = 'html'  
            email.send()
            return Response({'message': 'OTP sent to email'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_otp(request):
    otp = request.data.get('otp')
    user = get_user_model().objects.filter(otp=otp).first()
    if user and user.verify_otp(otp):
        user.otp = None
        user.otp_expires_at = None
        user.save()
        token, created = Token.objects.get_or_create(user=user)
        user_data = ClientSerializer(user).data
        return Response({'token': token.key, 'user': user_data}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def resend_otp(request):
    email = request.data.get('email')
    user = get_user_model().objects.filter(email=email).first()
    
    if user:
        otp = user.generate_otp()
        
        # Send OTP to the user
        subject = 'Your OTP Code'
        message = render_to_string('otp_email.html', {
            'otp_code': otp,
            'current_year': datetime.datetime.now().year
        })
        email_message = EmailMessage(subject, message, settings.EMAIL_FROM, [user.email])
        email_message.content_subtype = 'html'
        email_message.send()
        
        return Response({'message': 'OTP resent to email'}, status=status.HTTP_200_OK)
    
    return Response({'error': 'Email not found'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_with_token(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Client.objects.get(email=email)
    except Client.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

    if user.check_password(password):
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': ClientSerializer(user).data}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
# Forgot Password
@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')
    user = get_user_model().objects.filter(email=email).first()
    
    if user:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')

        subject = 'Password Reset Request'
        message = render_to_string('password_reset_email.html', {
            'user': user,
            'reset_link': reset_link,
        })
        email_message = EmailMessage(subject, message, settings.EMAIL_FROM, [user.email])
        email_message.send()

        return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
    
    return Response({'error': 'Email not found'}, status=status.HTTP_400_BAD_REQUEST)

# Reset Password
@api_view(['POST'])
def reset_password(request, uidb64, token):
    password = request.data.get('password')
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)

    if default_token_generator.check_token(user, token):
        user.set_password(password)
        user.save()
        return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)
    
    return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

# Update Profile
@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
def update_profile(request):
    serializer = ClientSerializer(request.user, data=request.data, partial=True)
    
    # If profile image is in request, handle it
    profile_image = request.FILES.get('profile_image')
    if profile_image:
        if hasattr(request.user, 'profile_image'):
            old_image = request.user.profile_image
            if old_image and default_storage.exists(old_image.path):
                default_storage.delete(old_image.path)

        request.user.profile_image = profile_image
        request.user.save()
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def register_with_insurance(request):
    client = request.user
    company_id = request.data.get('insurance_company')
    if company_id:
        client.insurance_company_id = company_id
        client.save()
        return Response({'message': 'Registered with insurance company'}, status=status.HTTP_200_OK)
    return Response({'error': 'Insurance company ID required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def subscribe_to_plan(request):
    plan_id = request.data.get('plan_id')
    if plan_id:
        try:
            plan = InsurancePlan.objects.get(id=plan_id)
            subscription, created = Subscription.objects.get_or_create(client=request.user, plan=plan)
            if created:
                return Response({'message': 'Subscribed to insurance plan'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Already subscribed to this plan'}, status=status.HTTP_200_OK)
        except InsurancePlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'error': 'Plan ID required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def unsubscribe_from_plan(request):
    plan_id = request.data.get('plan_id')
    if plan_id:
        try:
            plan = InsurancePlan.objects.get(id=plan_id)
            subscription = Subscription.objects.filter(client=request.user, plan=plan).first()
            if subscription:
                subscription.delete()
                return Response({'message': 'Unsubscribed from insurance plan'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Not subscribed to this plan'}, status=status.HTTP_400_BAD_REQUEST)
        except InsurancePlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'error': 'Plan ID required'}, status=status.HTTP_400_BAD_REQUEST)

# Client Profile
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def get_client_profile(request):
    serializer = ClientSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
def update_client_profile(request):
    serializer = ClientSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Health Data
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def get_health_data(request):
    data = HealthData.objects.filter(client=request.user)
    serializer = HealthDataSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def save_health_data(request):
    serializer = HealthDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(client=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Data Requests
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def get_data_requests(request):
    requests = DataRequest.objects.filter(client=request.user)
    serializer = DataRequestSerializer(requests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
def update_data_request_status(request, request_id):
    try:
        data_request = DataRequest.objects.get(id=request_id, client=request.user)
    except DataRequest.DoesNotExist:
        return Response({'error': 'Data request not found'}, status=status.HTTP_404_NOT_FOUND)

    status_value = request.data.get('status')
    if status_value not in ['approved', 'rejected']:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    data_request.status = status_value
    data_request.save()
    serializer = DataRequestSerializer(data_request)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Claims
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def get_claims(request):
    claims = Claim.objects.filter(client=request.user)
    serializer = ClaimSerializer(claims, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def submit_claim(request):
    data = request.data.copy()
    data['client'] = request.user.id  # Automatically set the client to the authenticated user
    data['status'] = 'pending'  # Set the initial status to 'pending'
    
    serializer = ClaimSerializer(data=data)
    if serializer.is_valid():
        serializer.save(client=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Insurance Plans
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def get_insurance_plans(request):
    if request.user.insurance_company:
        plans = InsurancePlan.objects.filter(insurancecompany=request.user.insurance_company)
        serializer = InsurancePlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'error': 'Client is not registered with any insurance company'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def get_subscribed_plans(request):
    user = request.user
    subscriptions = Subscription.objects.filter(client=user)
    serializer = SubscriptionSerializer(subscriptions, many=True)
    return Response(serializer.data)
# Credit Card
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def add_credit_card(request):
    serializer = CreditCardSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(client=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def get_credit_cards(request):
    cards = CreditCard.objects.filter(client=request.user)
    serializer = CreditCardSerializer(cards, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
def update_credit_card(request, card_id):
    try:
        card = CreditCard.objects.get(id=card_id, client=request.user)
    except CreditCard.DoesNotExist:
        return Response({'error': 'Credit card not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CreditCardSerializer(card, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
def delete_credit_card(request, card_id):
    try:
        card = CreditCard.objects.get(id=card_id, client=request.user)
        card.delete()
        return Response({'message': 'Credit card deleted'}, status=status.HTTP_204_NO_CONTENT)
    except CreditCard.DoesNotExist:
        return Response({'error': 'Credit card not found'}, status=status.HTTP_404_NOT_FOUND)
