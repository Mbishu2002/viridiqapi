# Generated by Django 5.0.8 on 2024-08-24 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Insurance', '0004_alter_insuranceplan_coverage_details_claimdocument'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='start_date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
