from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,  authentication_classes
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from .models import InsuranceCompany, InsurancePlan, Subscription
from .serializers import InsuranceCompanySerializer, LoginSerializer,  InsurancePlanSerializer, SubscriptionSerializer, InsuranceCompanyDetailSerializer, SubscriptionDetailSerializer
from Clients.models import Client, DataRequest,CustomToken
from Clients.serializers import ClientSerializer
from .utils import get_or_create_token
from Clients.customtokenauth import CustomTokenAuthentication

@api_view(['POST'])
def register_insurance_company(request):
    serializer = InsuranceCompanySerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_link = f'https://viridiqapi-latest.onrender.com/api/insurance/verify-email/{uid}/{token}/'
        
        subject = 'Activate your Insurance Company Account'
        message = render_to_string('verification_email.html', {
            'verification_link': verification_link,
        })
        email = EmailMessage(subject, message, settings.EMAIL_FROM, [user.email])  
        email.content_subtype = 'html'  
        email.send()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user =InsuranceCompany.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError,InsuranceCompany.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return Response({'detail': 'Email address has been verified.'}, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Verification link is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

    try:
        user = InsuranceCompany.objects.get(email=email)
    except ObjectDoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

    if user.check_password(password):
        token, created = CustomToken.objects.get_or_create(insurance_company=user)
        return Response({'token': token.key, 'user': InsuranceCompanySerializer(user).data}, status=status.HTTP_200_OK)
    else:
        return Response( serializer.data, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def list_clients(request):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    clients = Client.objects.filter(insurance_company=company)
    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def create_insurance_plan(request):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    data = request.data.copy()
    data['company'] = company.id
    serializer = InsurancePlanSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def view_client_profile(request, client_id):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    client = get_object_or_404(Client, id=client_id, insurance_company=company)
    serializer = ClientSerializer(client)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def update_claim_status(request, subscription_id):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    subscription = get_object_or_404(Subscription, id=subscription_id, plan__company=company)

    status = request.data.get('status')
    if status not in ['approved', 'rejected']:
        return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

    subscription.status = status
    subscription.save()
    return Response({'status': f'Claim {status}'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def request_client_data(request, client_id):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    client = get_object_or_404(Client, id=client_id, insurance_company=company)
    # Create a data request
    data_request = DataRequest.objects.create(insurance_company=company, client=client)
    return Response({'status': 'Data request created'}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def manage_subscriptions(request):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    subscriptions = Subscription.objects.filter(plan__company=company)
    serializer = SubscriptionDetailSerializer(subscriptions, many=True)
    return Response(serializer.data)

def email_confirmation(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = InsuranceCompany.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, user.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        success = True
    else:
        success = False

    return render(request, 'email_confirmation.html', {'success': success})
