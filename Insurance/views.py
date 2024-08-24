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
from .models import InsuranceCompany, InsurancePlan, Subscription, Claim
from .serializers import InsuranceCompanySerializer, LoginSerializer,  InsurancePlanSerializer, ClaimSerializer, SubscriptionSerializer, InsuranceCompanyDetailSerializer, SubscriptionDetailSerializer
from Clients.models import Client, DataRequest,CustomToken, HealthData, RiskProfile
from Clients.serializers import ClientSerializer,HealthDataSerializer, RiskProfileSerializer
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
    print(request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

    try:
        user = InsuranceCompany.objects.get(email=email)
    except ObjectDoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

    if user.check_password(password):
        token, created = CustomToken.objects.get_or_create(insurance_company=user)
        print(InsuranceCompanySerializer(user).data)
        return Response({'token': token.key, 'user': InsuranceCompanySerializer(user, context={'request': request}).data}, status=status.HTTP_200_OK)
    else:
        return Response( serializer.data, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def list_clients(request):
    company = get_object_or_404(InsuranceCompany, id=request.user.id)
    clients = Client.objects.filter(insurance_companies=company.id)
    serializer = ClientSerializer(clients, many=True, context={'request': request})
    print(serializer)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def create_insurance_plan(request):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    data = request.data.copy()
    data['company'] = company.id

    serializer = InsurancePlanSerializer(data=data)
    print(serializer)
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
def update_claim_status(request, claim_id):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    claim = get_object_or_404(Claim, id=claim_id, plan__company=company)

    status = request.data.get('status')
    if status not in ['approved', 'rejected']:
        return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

    claim.status = status
    claim.save()

    # Fetch the associated client
    client = get_object_or_404(Client, id=claim.client.id)

    # Sending an email notification to the client
    send_mail(
        'Claim Status Update',
        f'Your claim with ID {claim_id} has been {status}.',
        settings.EMAIL_FROM,  
        [client.email], 
        fail_silently=False,
    )

    return Response({'status': f'Claim {status}'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def request_client_data(request, client_id):
    # Get the insurance company associated with the current user
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    
    # Check if the client is associated with the insurance company
    client = get_object_or_404(Client, id=client_id)
    if not client.insurance_companies.filter(id=company.id).exists():
        return Response({'error': 'Client does not belong to this insurance company'}, status=status.HTTP_403_FORBIDDEN)
    
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

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def get_plan_by_id(request, plan_id):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    plan = get_object_or_404(InsurancePlan, id=plan_id, company=company)
    subscriptions = Subscription.objects.filter(plan=plan)
    
    client_ids = subscriptions.values_list('client', flat=True).distinct()
    clients = Client.objects.filter(id__in=client_ids)
    
    serializer = ClientSerializer(clients, many=True, context={'request': request})
    client_data = {client.id: data for client, data in zip(clients, serializer.data)}
    
    subscriber_data = [{
        'id': subscription.id,
        'client_name': client_data.get(subscription.client.id, {}).get('first_name', 'N/A'),
        'client_email': client_data.get(subscription.client.id, {}).get('email', 'N/A'),
        'client_profile': client_data.get(subscription.client.id, {}).get('profile_image', 'N/A'),
        'status': subscription.status
    } for subscription in subscriptions]
    
    plan_data = {
        'id': plan.id,
        'plan_name': plan.plan_name,
        'description': plan.description,
        'price': plan.price,
        'subscribers': subscriber_data
    }
    
    return Response(plan_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def list_plans_with_subscribers(request):
    company = get_object_or_404(InsuranceCompany, email=request.user.email)
    plans = InsurancePlan.objects.filter(company=company)
    
    # Create a list of dictionaries with plan details and subscriber count
    plan_data = []
    for plan in plans:
        subscriber_count = Subscription.objects.filter(plan=plan).count()
        plan_data.append({
            'id': plan.id,
            'plan_name': plan.plan_name,
            'price': plan.price,
            'description': plan.description,
            'subscribers': subscriber_count
        })
    
    return Response(plan_data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@authentication_classes([CustomTokenAuthentication])
def update_insurance_profile(request):
    # Get the insurance company using the email from the authenticated user
    company = get_object_or_404(InsuranceCompany, email=request.user.email)

    # Deserialize the incoming data
    serializer = InsuranceCompanySerializer(company, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def get_claims_by_company(request):
    # Use request.user.id to find the claims
    
    claims = Claim.objects.filter(plan__company__id=request.user.id)
    print(request.user.id)
    print(claims)
    serializer = ClaimSerializer(claims, many=True)
    print(serializer.data)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def get_client_profile(request, client_id):
    # Retrieve the authenticated user's email
    user_email = request.user.email

    # Check if the user is an insurance company
    try:
        company = InsuranceCompany.objects.get(email=user_email)
    except InsuranceCompany.DoesNotExist:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    # Check if there's an approved request for the client data
    approved_requests = DataRequest.objects.filter(insurance_company=company, status='approved')
    approved_client_ids = approved_requests.values_list('client_id', flat=True)

    # Fetch the client profile
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return Response({'error': 'Client profile not found'}, status=status.HTTP_404_NOT_FOUND)

    client_serializer = ClientSerializer(client, context={'request': request})
    response_data = {'client_profile': client_serializer.data}

    # If the company has access, provide health data and risk profile
    if client_id in approved_client_ids:
        # Fetch and serialize health data if access is approved
        health_data = HealthData.objects.filter(client=client)
        health_data_serializer = HealthDataSerializer(health_data, many=True)
        response_data['health_data'] = health_data_serializer.data

        # Fetch and serialize the risk profile
        try:
            risk_profile = RiskProfile.objects.get(client=client)
            risk_profile_serializer = RiskProfileSerializer(risk_profile)
            response_data['risk_profile'] = risk_profile_serializer.data
        except RiskProfile.DoesNotExist:
            response_data['risk_profile'] = 'Risk profile not available'

    else:
        # If access is not approved, create a data request
        data_request, created = DataRequest.objects.get_or_create(
            insurance_company=company,
            client=client,
            defaults={'status': 'pending'}
        )

        if created:
            message = 'Access to health data and risk profile requested. You will be notified once the request is approved.'
        else:
            message = 'Access to health data and risk profile is still pending approval.'

        response_data['message'] = message

    return Response(response_data, status=status.HTTP_200_OK)
