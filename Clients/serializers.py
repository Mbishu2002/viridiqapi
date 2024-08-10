from rest_framework import serializers
from .models import Client, HealthData, DataRequest, CreditCard
from Insurance.models import InsuranceCompany

class ClientSerializer(serializers.ModelSerializer):
    insurance_companies = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=InsuranceCompany.objects.all(),         
        required=False,  
        allow_null=True)

    class Meta:
        model = Client
        fields = ['first_name','email','password', 'profile_image', 'insurance_companies', 'otp']
        extra_kwargs = {
            'password': {'write_only': True},
        }

class HealthDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthData
        fields = ['__all__']

class DataRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataRequest
        fields = ['__all___']

class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = ['__all__']
