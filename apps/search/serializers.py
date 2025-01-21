from rest_framework import serializers
from apps.users.models import User
from apps.contacts.models import Contact
from apps.spam.models import SpamReport

class SearchResultSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone_number = serializers.CharField()
    spam_likelihood = serializers.FloatField()
    is_registered_user = serializers.BooleanField()
    email = serializers.EmailField(allow_null=True, required=False)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        # Handle email visibility
        if data.get('is_registered_user') and request:
            user = User.objects.filter(phone_number=data['phone_number']).first()
            if user and request.user != user:
                # Only show email if requester is in user's contacts
                if not user.contacts.filter(phone_number=request.user.phone_number).exists():
                    data['email'] = None

        return data

class PhoneSearchResultSerializer(SearchResultSerializer):
    """
    Specific serializer for phone number search results
    Includes all names associated with the phone number
    """
    associated_names = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )