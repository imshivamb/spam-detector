from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    TokenRefreshSerializer,
    PasswordChangeSerializer
)
from .models import User

class AuthViewSet(viewsets.GenericViewSet):
    permission_classes=[AllowAny]
    
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """Handle user registration"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'id': str(user.id),
                    'name': user.name,
                    'phone_number': user.phone_number,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': 'Registration failed',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """Handle user login"""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = authenticate(
                    phone_number=serializer.validated_data['phone_number'],
                    password=serializer.validated_data['password']
                )
                if user:
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                        'user': {
                            'id': str(user.id),
                            'name': user.name,
                            'phone_number': user.phone_number,
                            'email': user.email
                        }
                    })
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({
                    'error': 'Login failed',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='refresh')
    def token_refresh(self, request):
        """Handle token refresh"""
        serializer = TokenRefreshSerializer(data=request.data)
        if serializer.is_valid():
            try:
                return Response({
                    'access_token': serializer.validated_data['access']
                })
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """Handle user logout"""
        try:
            # Get refresh token from request
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Clear user's cached data
            cache_key = f'user_tokens_{request.user.id}'
            cache.delete(cache_key)
            
            return Response({
                'status': 'success',
                'message': 'Successfully logged out'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
class UserViewSet(viewsets.ModelViewSet):
    permission_classes= [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        """Override to ensure users can only access their own profile"""
        return self.request.user
    
    @action(detail=False, methods=['get', 'put', 'patch'], url_path='profile')
    def profile(self, request):
        """Handle both GET and PUT/PATCH for profile"""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:  # PUT or PATCH
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """Change user password"""
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                
                # Invalidate existing tokens
                cache_key = f'user_tokens_{user.id}'
                cache.delete(cache_key)
                
                return Response({
                    'status': 'success',
                    'message': 'Password updated successfully'
                })
            return Response({
                'error': 'Invalid old password'
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'], url_path='deactivate')
    def deactivate_account(self, request):
        """Deactivate user account"""
        try:
            user = request.user
            # Verify password before deactivation
            password = request.data.get('password')
            if not password or not user.check_password(password):
                return Response({
                    'error': 'Invalid password'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Deactivate account
            user.is_active = False
            user.save()

            # Blacklist all tokens
            cache_key = f'user_tokens_{user.id}'
            cache.delete(cache_key)

            return Response({
                'status': 'success',
                'message': 'Account deactivated successfully'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)