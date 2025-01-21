from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as JWTTokenRefreshSerializer

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('id', 'name', 'phone_number', 'email', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': False},
            'phone_number': {'required': True},
            'name': {'required': True}
        }
        
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            name=validated_data['name'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user
    
class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'phone_number', 'email')
        extra_kwargs = {
            'phone_number': {'read_only': True},
            'email': {'read_only': True},
        }

    def to_representation(self, instance):
        """
        Override to control email visibility based on contact list
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Hide email unless requester is in user's contacts
        if request and request.user != instance:
            if not instance.contacts.filter(phone_number=request.user.phone_number).exists():
                data.pop('email', None)
        
        return data
    
class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "New password fields didn't match."
            })
        return attrs

class TokenRefreshSerializer(JWTTokenRefreshSerializer):
    """
    Serializer for token refresh
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        return data