from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from rest_framework import status
from django.utils.encoding import force_bytes, force_str
from django.core.files.storage import default_storage
from django.contrib.auth.tokens import default_token_generator
from rest_framework.authtoken.models import Token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.files.storage import default_storage
import pyotp
from django.http import JsonResponse
from django.contrib.auth.forms import SetPasswordForm
from .models import HealthData, DataRequest, CreditCard, Client, CustomToken
from .serializers import ClientSerializer, HealthDataSerializer, DataRequestSerializer, CreditCardSerializer, LoginSerializer
from Insurance.models import Claim, InsurancePlan, Subscription, InsuranceCompany, ClaimDocument
from Insurance.serializers import ClaimSerializer, InsurancePlanSerializer, SubscriptionSerializer, InsuranceCompanySerializer
from django.conf import settings
import datetime
from .customtokenauth import CustomTokenAuthentication

# Registration views
@api_view(['POST'])
def register_client(request):
    serializer = ClientSerializer(data=request.data)
    print(request.data)

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
    email = request.data.get('email')
    user = Client.objects.filter(email=email).first()
    print(request.data)

    if user and user.verify_otp(otp):
        print(user.verify_otp(otp))
        user.otp = None
        user.otp_expires_at = None
        user.save()
        token, created = CustomToken.objects.get_or_create(client=user)
        user_data = ClientSerializer(user, context={'request': request}).data
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
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            user = Client.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if user.check_password(password):
            token, created = CustomToken.objects.get_or_create(client=user)
            user_data = ClientSerializer(user, context={'request': request}).data
            
            # user_data = {
            #     'email': user.email,
            #     'first_name': user.first_name,
            #     'profile_image': user.profile_image.url if user.profile_image else None,
            # }
            
            return Response({'token': token.key, 'user': user_data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# Forgot Password
@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')
    user = get_user_model().objects.filter(email=email).first()
    
    if user:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f'https://viridiqapi-latest.onrender.com/api/clients/reset-password/{uid}/{token}/'

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
@api_view(['PATCH', 'PUT'])
@authentication_classes([CustomTokenAuthentication])
def update_profile(request):
    user_id = request.user.id
    print(user_id)
    try:
        user = Client.objects.get(id=user_id)
    except Client.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Create an instance of the serializer with the user instance and request data
    serializer = ClientSerializer(user, data=request.data, partial=True, context={'request': request})

    # Handle profile image if present in the request
    profile_image = request.FILES.get('profile_image')
    if profile_image:
        # Handle old profile image if it exists
        if user.profile_image and default_storage.exists(user.profile_image.path):
            default_storage.delete(user.profile_image.path)
        
        # Update the request data with the new profile image
        request.data._mutable = True
        request.data['profile_image'] = profile_image
        request.data._mutable = False

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def register_with_insurance(request):
    client = request.user
    company_id = request.data.get('insurance_company')
    if company_id:
        client.insurance_company_id = company_id
        client.save()
        return Response({'message': 'Registered with insurance company'}, status=status.HTTP_200_OK)
    return Response({'error': 'Insurance company ID required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
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
@authentication_classes([CustomTokenAuthentication])
def unsubscribe_from_plan(request):
    plan_id = request.data.get('plan_id')
    
    if not plan_id:
        return Response({'error': 'Plan ID required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        plan = InsurancePlan.objects.get(id=plan_id)
        subscription = Subscription.objects.filter(client=request.user, plan=plan).first()
        
        if subscription:
            # Set end_date to now to mark the subscription as ended
            subscription.end_date = timezone.now()
            subscription.save()
            return Response({'message': 'Unsubscribed from insurance plan'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Not subscribed to this plan'}, status=status.HTTP_400_BAD_REQUEST)
    
    except InsurancePlan.DoesNotExist:
        return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

# Client Profile
@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def get_client_profile(request):
    serializer = ClientSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)



# Health Data
@api_view(['GET'])
def get_health_data(request):
    data = HealthData.objects.filter(client=request.user)
    serializer = HealthDataSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def save_health_data(request):
    data = request.data
    data['client'] = request.user.id  

    serializer = HealthDataSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def get_data_requests(request):
    # Fetch data requests for the authenticated user
    requests = DataRequest.objects.filter(client=request.user.id)
    print(request.user.id)

    # Prepare the response data
    data = []
    for req in requests:
        # Fetch the related insurance company
        company_name = 'Unknown'
        if req.insurance_company:
            try:
                company = InsuranceCompany.objects.get(id=req.insurance_company.id)
                company_name = company.company_name
            except InsuranceCompany.DoesNotExist:
                company_name = 'Unknown'

        data.append({
            'id': req.id,
            'insurance_company': company_name,
            'timestamp': req.timestamp.isoformat(),  
            'status': req.status,
        })

    return Response(data, status=status.HTTP_200_OK)
@api_view(['PATCH'])
@authentication_classes([CustomTokenAuthentication])
def update_data_request_status(request, request_id):
    try:
        data_request = DataRequest.objects.get(id=request_id, client=request.user.id)
    except DataRequest.DoesNotExist:
        return Response({'error': 'Data request not found'}, status=status.HTTP_404_NOT_FOUND)

    status_value = request.data.get('status')
    if status_value not in ['approved', 'rejected']:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    data_request.status = status_value
    data_request.save()
    serializer = DataRequestSerializer(data_request, partial=True)
    return Response(serializer.data, status=status.HTTP_200_OK)




@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def submit_claim(request):
    data = request.data.copy()
    data['client'] = request.user.id
    data['status'] = 'pending'
    
    # Handle files separately
    documents = request.FILES.getlist('documents')

    # Initialize the serializer with the data
    serializer = ClaimSerializer(data=data)
    
    if serializer.is_valid():
        claim = serializer.save()
        
        # Save each document if there are any
        for document in documents:
            ClaimDocument.objects.create(
                claim=claim,
                document=document
            )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def get_insurance_plans(request):
    if request.user.insurance_companies.exists():
        plans = InsurancePlan.objects.filter(company__in=request.user.insurance_companies.all())
        
        plans_with_subscription = [
            {
                'id': plan.id,
                'plan_name': plan.plan_name,
                'description': plan.description,
                'price': plan.price,
                'subscribed': Subscription.objects.filter(client=request.user, plan=plan).exists()
            }
            for plan in plans
        ]
        
        return Response(plans_with_subscription, status=status.HTTP_200_OK)
    
    return Response({'error': 'No insurance companies found for this user'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def get_subscribed_plans(request):
    user = request.user
    subscriptions = Subscription.objects.filter(client=user)
    serializer = SubscriptionSerializer(subscriptions, many=True)
    return Response(serializer.data)
# Credit Card
@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
def add_credit_card(request):
    serializer = CreditCardSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(client=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
def get_credit_cards(request):
    cards = CreditCard.objects.filter(client=request.user)
    serializer = CreditCardSerializer(cards, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@authentication_classes([CustomTokenAuthentication])
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
@authentication_classes([CustomTokenAuthentication])
def delete_credit_card(request, card_id):
    try:
        card = CreditCard.objects.get(id=card_id, client=request.user)
        card.delete()
        return Response({'message': 'Credit card deleted'}, status=status.HTTP_204_NO_CONTENT)
    except CreditCard.DoesNotExist:
        return Response({'error': 'Credit card not found'}, status=status.HTTP_404_NOT_FOUND)
    
def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, user.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse({'message': 'Password has been reset'}, status=200)
        else:
            form = SetPasswordForm(user)
        
        return render(request, 'password_change.html', {'form': form})
    
    return JsonResponse({'error': 'Invalid or expired token'}, status=400)

@api_view(['GET'])
def insurance_company_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        # Perform a case-insensitive search using LIKE
        companies = InsuranceCompany.objects.filter(company_name__icontains=search_query)[:10]
    else:
        # Return the first 10 companies if no search query is provided
        companies = InsuranceCompany.objects.all().order_by('company_name')[:10]

    serializer = InsuranceCompanySerializer(companies, many=True)
    return Response(serializer.data)