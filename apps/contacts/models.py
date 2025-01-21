from django.db import models
import uuid
from django.core.validators import RegexValidator
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector

class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='contacts', db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    name_search_vector = SearchVectorField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contacts'
        indexes = [
            models.Index(fields=['phone_number', 'user']),
            models.Index(fields=['name', 'user']),
            GinIndex(fields=['name_search_vector']),
        ]
        ordering = ['-created_at']
        unique_together = ['user', 'phone_number']

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

    def save(self, *args, **kwargs):
        """Override save to ensure phone number is standardized"""
        if self.phone_number:
            self.phone_number = self.phone_number.strip().replace(" ", "")
        super().save(*args, **kwargs)

@receiver(post_save, sender=Contact)
def update_search_vector(sender, instance, **kwargs):
    """Update search vector when contact is saved"""
    Contact.objects.filter(pk=instance.pk).update(
        name_search_vector=SearchVector('name')
    )
