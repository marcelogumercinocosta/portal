# Generated by Django 3.2 on 2021-06-10 17:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('noc', '0002_checklist_enviado'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='checklist',
            name='alerta_equipamento',
        ),
        migrations.DeleteModel(
            name='ChecklistOcorrencia',
        ),
    ]
