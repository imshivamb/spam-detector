from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count

from .models import SpamReport
from .serializers import (
    SpamReportSerializer,
    SpamStatusSerializer,
    SpamStatisticsSerializer
)

class SpamViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SpamReportSerializer

    @action(detail=False, methods=['post'], url_path='report')
    def report_spam(self, request):
        """Report a number as spam"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            spam_report = SpamReport.objects.create(
                reporter=request.user,
                phone_number=serializer.validated_data['phone_number'],
                is_active=True
            )
            
            spam_likelihood = SpamReport.get_spam_likelihood(
                spam_report.phone_number
            )
            
            return Response({
                'status': 'success',
                'message': 'Number reported as spam',
                'current_spam_likelihood': spam_likelihood,
                'report_id': str(spam_report.id)
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='retract')
    def retract_report(self, request, pk=None):
        """Retract a spam report"""
        try:
            report = SpamReport.objects.get(
                reporter=request.user,
                phone_number=pk,
                is_active=True
            )
            report.is_active = False
            report.save()
            
            spam_likelihood = SpamReport.get_spam_likelihood(pk)
            
            return Response({
                'status': 'success',
                'message': 'Spam report retracted successfully',
                'current_spam_likelihood': spam_likelihood
            }, status=status.HTTP_200_OK)
            
        except SpamReport.DoesNotExist:
            return Response({
                'error': 'No active spam report found for this number'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='status/(?P<phone_number>[^/.]+)')
    def spam_status(self, request, phone_number=None):
        """Get spam status for a phone number"""
        try:
            spam_likelihood = SpamReport.get_spam_likelihood(phone_number)
            total_reports = SpamReport.objects.filter(
                phone_number=phone_number,
                is_active=True
            ).count()
            
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recent_reports = SpamReport.objects.filter(
                phone_number=phone_number,
                is_active=True,
                reported_at__gte=thirty_days_ago
            ).count()
            
            data = {
                'phone_number': phone_number,
                'spam_likelihood': spam_likelihood,
                'total_reports': total_reports,
                'recent_reports_count': recent_reports
            }
            
            serializer = SpamStatusSerializer(
                data=data,
                context={'request': request}
            )
            if serializer.is_valid():
                return Response(serializer.data)
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='statistics')
    def get_statistics(self, request):
        """Get overall spam reporting statistics"""
        try:
            today = timezone.now().date()
            week_ago = today - timezone.timedelta(days=7)
            month_ago = today - timezone.timedelta(days=30)

            stats = {
                'total_reports': SpamReport.objects.filter(is_active=True).count(),
                'reports_today': SpamReport.objects.filter(
                    is_active=True,
                    reported_at__date=today
                ).count(),
                'reports_this_week': SpamReport.objects.filter(
                    is_active=True,
                    reported_at__date__gte=week_ago
                ).count(),
                'reports_this_month': SpamReport.objects.filter(
                    is_active=True,
                    reported_at__date__gte=month_ago
                ).count(),
                'most_reported_numbers': SpamReport.objects.filter(
                    is_active=True
                ).values('phone_number').annotate(
                    report_count=Count('id')
                ).order_by('-report_count')[:10],
                'spam_likelihood_distribution': {
                    'high': SpamReport.objects.filter(
                        is_active=True
                    ).values('phone_number').annotate(
                        count=Count('id')
                    ).filter(count__gte=10).count(),
                    'medium': SpamReport.objects.filter(
                        is_active=True
                    ).values('phone_number').annotate(
                        count=Count('id')
                    ).filter(count__range=(5, 9)).count(),
                    'low': SpamReport.objects.filter(
                        is_active=True
                    ).values('phone_number').annotate(
                        count=Count('id')
                    ).filter(count__lt=5).count()
                }
            }

            serializer = SpamStatisticsSerializer(
                data=stats,
                context={'request': request}
            )
            if serializer.is_valid():
                return Response(serializer.data)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)