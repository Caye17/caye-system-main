# Generated by Django 5.2.1 on 2025-05-26 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_loan_approved_at_loan_approved_by_loan_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='quantity',
            field=models.PositiveIntegerField(default=1, help_text='Number of copies available'),
        ),
    ]
