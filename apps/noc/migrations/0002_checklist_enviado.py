# Generated by Django 3.2 on 2021-06-10 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('noc', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='checklist',
            name='enviado',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
