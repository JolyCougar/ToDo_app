# Generated by Django 5.1.1 on 2024-10-21 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_auth', '0006_profile_telegram_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='telegram_username',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
