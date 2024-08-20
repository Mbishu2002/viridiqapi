from rest_framework import serializers
from .models import InsuranceCompany, InsurancePlan, Subscription, Claim
from Clients.serializers import ClientSerializer

class InsuranceCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCompany
        fields = ['id', 'company_name', 'logo', 'phone_number', 'location', 'email', 'address', 'website', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = super().create(validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

class InsurancePlanSerializer(serializers.ModelSerializer):
    company = serializers.StringRelatedField()  

    class Meta:
        model = InsurancePlan
        fields = ['id', 'company', 'plan_name', 'description', 'coverage_details', 'price', 'created_at', 'updated_at']

class SubscriptionSerializer(serializers.ModelSerializer):
    client = serializers.StringRelatedField()  
    plan = serializers.StringRelatedField()  

    class Meta:
        model = Subscription
        fields = ['id', 'client', 'plan', 'start_date', 'end_date', 'status']

class ClaimSerializer(serializers.ModelSerializer):
    client = serializers.StringRelatedField(read_only=True)
    plan = serializers.PrimaryKeyRelatedField(queryset=InsurancePlan.objects.all())

    class Meta:
        model = Claim
        fields = ['id', 'client','plan', 'amount_claimed', 'status', 'date_submitted', 'description']
        read_only_fields = ['status', 'date_submitted']
class InsuranceCompanyDetailSerializer(serializers.ModelSerializer):
    plans = InsurancePlanSerializer(many=True, read_only=True)

    class Meta:
        model = InsuranceCompany
        fields = ['id', 'company_name', 'logo', 'phone_number', 'location', 'email', 'address', 'website']

class SubscriptionDetailSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    plan = InsurancePlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'client', 'plan', 'start_date', 'end_date', 'status']



 
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)