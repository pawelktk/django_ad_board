# Generated by Django 5.1.7 on 2025-04-07 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0007_userrecommendation'),
    ]

    operations = [
        migrations.AddField(
            model_name='userrecommendation',
            name='is_reported',
            field=models.BooleanField(default=False),
        ),
    ]
