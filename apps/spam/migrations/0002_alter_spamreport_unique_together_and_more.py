# Generated by Django 5.0.1 on 2025-01-14 16:24

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("spam", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="spamreport",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="spamreport",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_active", True)),
                fields=("reporter", "phone_number"),
                name="unique_active_report",
            ),
        ),
    ]
