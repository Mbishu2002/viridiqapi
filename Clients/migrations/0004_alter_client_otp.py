# Generated by Django 5.0.8 on 2024-08-11 23:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Clients', '0003_remove_client_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='otp',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
