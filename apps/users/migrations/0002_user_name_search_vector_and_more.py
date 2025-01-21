# Generated by Django 5.0.1 on 2025-01-14 14:21

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="name_search_vector",
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name="user",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["name_search_vector"], name="users_name_se_eddb22_gin"
            ),
        ),
    ]
