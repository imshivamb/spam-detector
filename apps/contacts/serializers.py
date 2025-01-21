from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import Contact
from apps.spam.models import SpamReport

class ContactSerializer(serializers.ModelSerializer):
    spam_likelihood = serializers.FloatField(read_only=True, required=False)
    
    class Meta:
        model = Contact
        fields = ['id', 'name', 'phone_number', 'created_at', 'updated_at', 'spam_likelihood']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'phone_number': {'required': False}
        }

    def validate_phone_number(self, value):
        """
        Validate phone number format
        """
        phone_regex = RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )
        try:
            phone_regex(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        """
        Check that the contact is not a duplicate for this user
        """
        request = self.context.get('request')
        if request and request.user:

            phone_number = data.get('phone_number')

            if phone_number is None and self.instance:
                phone_number = self.instance.phone_number
            
            if phone_number:
                existing_contact = Contact.objects.filter(
                    user=request.user,
                    phone_number=phone_number
                ).exclude(id=getattr(self.instance, 'id', None))
                
                if existing_contact.exists():
                    raise serializers.ValidationError(
                        {"phone_number": "You already have a contact with this phone number."}
                    )
        return data

    def to_representation(self, instance):
        """
        Add spam likelihood to the response
        """
        data = super().to_representation(instance)
        data['spam_likelihood'] = SpamReport.get_spam_likelihood(instance.phone_number)
        return data

class ContactBulkCreateSerializer(ContactSerializer):
    class Meta(ContactSerializer.Meta):
        fields = ['name', 'phone_number']

    def create(self, validated_data):
        """
        Create a new contact instance with user from context
        """
        user = self.context['request'].user
        return Contact.objects.create(user=user, **validated_data)

class ContactDetailSerializer(ContactSerializer):
    """
    Serializer for detailed contact view including additional information
    """
    is_registered_user = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)

    class Meta(ContactSerializer.Meta):
        fields = ContactSerializer.Meta.fields + ['is_registered_user', 'email']

    def get_is_registered_user(self, obj):
        """
        Check if this contact is a registered user
        """
        from apps.users.models import User
        return User.objects.filter(phone_number=obj.phone_number).exists()

    def to_representation(self, instance):
        """
        Add registered user information and handle email visibility
        """
        data = super().to_representation(instance)
        
        # If contact is a registered user, try to get their email
        if data['is_registered_user']:
            from apps.users.models import User
            user = User.objects.get(phone_number=instance.phone_number)
            
            # Only include email if the requesting user is in the contact's contact list
            request_user = self.context.get('request').user
            if user.contacts.filter(phone_number=request_user.phone_number).exists():
                data['email'] = user.email
            else:
                data['email'] = None
        
        return data

class ContactSearchSerializer(ContactSerializer):
    """
    Serializer for search results with additional spam information
    """
    total_spam_reports = serializers.SerializerMethodField()

    class Meta(ContactSerializer.Meta):
        fields = ContactSerializer.Meta.fields + ['total_spam_reports']

    def get_total_spam_reports(self, obj):
        """
        Get total number of spam reports for this contact's number
        """
        return SpamReport.objects.filter(
            phone_number=obj.phone_number,
            is_active=True
        ).count()