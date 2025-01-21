from rest_framework import serializers
from .models import SpamReport
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import ExtractWeekDay, ExtractHour

class SpamReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpamReport
        fields = ['id', 'phone_number', 'reported_at']
        read_only_fields = ['id', 'reported_at']
        
    def validate_phone_number(self, value):
        """Validate phone number isn't user's own number"""
        request = self.context.get('request')
        if request and request.user and request.user.phone_number == value:
            raise serializers.ValidationError(
                "You cannot mark your own number as spam."
            )
        return value
    
    def validate(self, data):
        """Check if user has already reported this number"""
        request = self.context.get('request')
        if request and request.user:
            existing_report = SpamReport.objects.filter(
                reporter=request.user,
                phone_number=data['phone_number'],
                is_active=True
            ).exists()
            if existing_report:
                raise serializers.ValidationError(
                    "You have already reported this number as spam."
                )
        return data

class SpamStatusSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    spam_likelihood = serializers.FloatField()
    total_reports = serializers.IntegerField()
    reported_by_user = serializers.SerializerMethodField()
    recent_reports_count = serializers.SerializerMethodField()
    is_user_contact = serializers.SerializerMethodField()
    
    def get_reported_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return SpamReport.objects.filter(
                reporter=request.user,
                phone_number=obj['phone_number'],
                is_active=True
            ).exists()
        return False
    
    def get_recent_reports_count(self, obj):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return SpamReport.objects.filter(
            phone_number=obj['phone_number'],
            is_active=True,
            reported_at__gte=thirty_days_ago
        ).count()
        
    def get_is_user_contact(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return request.user.contacts.filter(
                phone_number=obj['phone_number']
            ).exists()
        return False

class SpamStatisticsSerializer(serializers.Serializer):
    total_reports = serializers.IntegerField()
    reports_today = serializers.IntegerField()
    reports_this_week = serializers.IntegerField()
    reports_this_month = serializers.IntegerField()
    most_reported_numbers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    spam_likelihood_distribution = serializers.DictField(
        child=serializers.IntegerField()
    )
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update({
            'reports_by_day_of_week': self._get_reports_by_day_of_week(),
            'peak_reporting_hours': self._get_peak_reporting_hours(),
        })
        return data
    
    def _get_reports_by_day_of_week(self):
        return SpamReport.objects.annotate(
            day=ExtractWeekDay('reported_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
    
    def _get_peak_reporting_hours(self):
        return SpamReport.objects.annotate(
            hour=ExtractHour('reported_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('-count')[:5]