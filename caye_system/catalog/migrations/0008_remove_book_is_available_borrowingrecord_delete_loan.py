# Generated by Django 5.2.1 on 2025-05-26 09:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_borrowrequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='is_available',
        ),
        migrations.CreateModel(
            name='BorrowingRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('borrow_date', models.DateField(auto_now_add=True)),
                ('due_date', models.DateField()),
                ('return_date', models.DateField(blank=True, null=True)),
                ('returned', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('returned', 'Returned')], default='pending', max_length=10)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.book')),
                ('borrower', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.borrower')),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_borrowing_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Borrowing Record',
                'verbose_name_plural': 'Borrowing Records',
                'ordering': ['borrow_date'],
            },
        ),
        migrations.DeleteModel(
            name='Loan',
        ),
    ]
