from rest_framework import serializers
from .models import Client, HealthData, DataRequest, CreditCard, RiskProfile
from Insurance.models import InsuranceCompany
from django.core.files.storage import default_storage
class ClientSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()  
    insurance_companies = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=InsuranceCompany.objects.all(),         
        required=False,  
        allow_null=True
    )

    class Meta:
        model = Client
        fields = ['id', 'first_name', 'email', 'password', 'profile_image', 'insurance_companies', 'otp']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_profile_image(self, obj):  
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return None

    def update(self, instance, validated_data):
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class HealthDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthData
        fields = ['client', 'data', 'timestamp'] 
class DataRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataRequest
        fields = ['id', 'insurance_company', 'timestamp', 'status']



class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = ['__all__']

class RiskProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskProfile
        fields = ['risk_level']

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
