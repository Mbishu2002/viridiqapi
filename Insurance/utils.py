from rest_framework.authtoken.models import Token
from Clients.models import Client
from .models import InsuranceCompany

def get_or_create_token(user):
    if isinstance(user, Client) or isinstance(user, InsuranceCompany):
        token, created = Token.objects.get_or_create(user=user)
        return token, created
    else:
        raise ValueError("Unsupported user type")
