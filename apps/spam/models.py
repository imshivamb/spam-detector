from django.db import models
import uuid
from django.core.validators import RegexValidator
from django.apps import apps
from django.core.cache import cache

class SpamReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='spam_reports')
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        db_index=True
    )
    reported_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'spam_reports'
        indexes = [
            models.Index(fields=['phone_number', 'is_active']),
            models.Index(fields=['reporter', 'phone_number', 'is_active']),
            models.Index(fields=['reported_at', 'is_active']),
        ]
        ordering = ['-reported_at']
        constraints = [
            models.UniqueConstraint(
                fields=['reporter', 'phone_number'],
                condition=models.Q(is_active=True),
                name='unique_active_report'
            )
        ]

    def __str__(self):
        return f"Spam report for {self.phone_number}"
    
    @classmethod
    def get_spam_likelihood(cls, phone_number):
        """
        Calculate spam likelihood for a phone number
        Returns percentage based on number of active reports
        """
        cache_key = f'spam_likelihood_{phone_number}'
        cache.delete(cache_key)
        likelihood = cache.get(cache_key)
        
        if likelihood is None:
            total_reports = cls.objects.filter(
                phone_number=phone_number,
                is_active=True
            ).count()

            if total_reports == 0:
                likelihood = 0.0
            else:
                likelihood = min((total_reports / 5) * 100, 100)
            
            cache.set(cache_key, likelihood, timeout=3600)  # 1 hour

        return likelihood