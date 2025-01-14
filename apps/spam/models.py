from django.db import models
import uuid
from django.core.validators import RegexValidator
from django.db.models import Count
from django.apps import apps

class SpamReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='spam_reports')
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'spam_reports'
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['reporter']),
            models.Index(fields=['reported_at']),
        ]
        ordering = ['-reported_at']
        # Prevent multiple reports from same user for same number
        unique_together = ['reporter', 'phone_number']

    def __str__(self):
        return f"Spam report for {self.phone_number}"
    
    @classmethod
    def get_spam_likelihood(cls, phone_number):
        """
        Calculate spam likelihood for a phone number
        Returns percentage of users who marked this number as spam
        """
        User = apps.get_model('users', 'User')
        total_users = User.objects.count()
        if total_users == 0:
            return 0.0
        
        spam_reports = cls.objects.filter(
            phone_number=phone_number,
            is_active=True
        ).count()
        
        # Calculate percentage with 2 decimal places
        likelihood = round((spam_reports / total_users) * 100, 2)
        return min(likelihood, 100.0)

