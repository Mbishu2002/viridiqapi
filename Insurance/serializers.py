from rest_framework import serializers
from .models import InsuranceCompany, InsurancePlan, Subscription, Claim
from Clients.serializers import ClientSerializer
from rest_framework import serializers
from .models import InsuranceCompany, ClaimDocument

class InsuranceCompanySerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()  

    class Meta:
        model = InsuranceCompany
        fields = ['id', 'company_name', 'logo', 'phone_number', 'location', 'email', 'address', 'website', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_logo(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)  
        return None

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
    company = serializers.PrimaryKeyRelatedField(queryset=InsuranceCompany.objects.all())

    class Meta:
        model = InsurancePlan
        fields = ['id', 'company', 'plan_name', 'description', 'coverage_details', 'price', 'created_at', 'updated_at']

    coverage_details = serializers.CharField(
        style={'base_template': 'textarea.html'},
        required=False,
        allow_blank=True
    )
class SubscriptionSerializer(serializers.ModelSerializer):
    client = serializers.StringRelatedField()  
    plan = serializers.StringRelatedField()  

    class Meta:
        model = Subscription
        fields = ['id', 'client', 'plan', 'start_date', 'end_date', 'status']

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimDocument
        fields = ['id', 'document', 'uploaded_at']

class ClaimSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Claim
        fields = ['id', 'client', 'plan', 'amount_claimed', 'status', 'date_submitted', 'description', 'documents']
        read_only_fields = ['status', 'date_submitted']
        extra_kwargs = {
            'client': {'write_only': True},
            'plan': {'required': True},  # Ensure 'plan' is required for creation
        }

    def create(self, validated_data):
        documents_data = validated_data.pop('documents', [])
        claim = Claim.objects.create(**validated_data)
        
        for document_data in documents_data:
            ClaimDocument.objects.create(claim=claim, **document_data)
        
        return claim

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