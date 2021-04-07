# Generated by Django 3.0.8 on 2021-04-06 21:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('infra', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Prometheus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jobname', models.CharField(max_length=255, verbose_name='nome')),
                ('porta', models.IntegerField(verbose_name='prioridade')),
            ],
        ),
        migrations.CreateModel(
            name='QuotaUtilizada',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limite', models.DecimalField(blank=True, decimal_places=0, max_digits=20, null=True, verbose_name='Limite')),
                ('quota', models.DecimalField(blank=True, decimal_places=0, max_digits=20, null=True, verbose_name='Quota')),
                ('usado', models.DecimalField(blank=True, decimal_places=0, max_digits=20, null=True, verbose_name='Usado')),
                ('storage_grupo_trabalho', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='infra.StorageAreaGrupoTrabalho')),
            ],
        ),
        migrations.CreateModel(
            name='TipoMonitoramento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='nome')),
            ],
            options={
                'verbose_name': 'Tipo',
                'verbose_name_plural': 'Tipos',
                'ordering': ('nome',),
            },
        ),
        migrations.CreateModel(
            name='StorageHistorico',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disco_used', models.DecimalField(decimal_places=2, max_digits=20)),
                ('atualizacao', models.DateTimeField(blank=True, null=True, verbose_name='Atualização')),
                ('storage_grupo_trabalho', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='infra.StorageAreaGrupoTrabalho')),
            ],
        ),
        migrations.CreateModel(
            name='QuotaUtilizadaLista',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(blank=True, max_length=50, null=True)),
                ('conta', models.CharField(blank=True, max_length=50, null=True)),
                ('usado', models.DecimalField(blank=True, decimal_places=0, max_digits=20, null=True, verbose_name='Usado')),
                ('detalhe', models.CharField(blank=True, max_length=50, null=True)),
                ('quota_utilizada', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitoramento.QuotaUtilizada')),
            ],
        ),
        migrations.CreateModel(
            name='Monitoramento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='nome')),
                ('url', models.URLField(verbose_name='url')),
                ('prioridade', models.IntegerField(verbose_name='prioridade')),
                ('target', models.CharField(choices=[('_blank', 'nova aba'), (' ', 'sem target')], max_length=10, verbose_name='target')),
                ('tipo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitoramento.TipoMonitoramento')),
            ],
            options={
                'verbose_name': 'Monitoramento',
                'verbose_name_plural': 'Monitoramentos',
                'ordering': ('tipo', 'prioridade', 'nome'),
            },
        ),
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.CharField(default='Volume', max_length=255)),
                ('snap', models.DecimalField(decimal_places=2, max_digits=20, verbose_name='Snap')),
                ('porcentagem_snap', models.IntegerField(verbose_name='Snap (%)')),
                ('snapshot_autodelete', models.CharField(blank=True, max_length=50, null=True)),
                ('snapshot_size_used', models.IntegerField(verbose_name='Snap Usado (%)')),
                ('snapshot_policy', models.CharField(blank=True, max_length=255, null=True)),
                ('total_disco', models.DecimalField(decimal_places=2, max_digits=20)),
                ('disco', models.DecimalField(decimal_places=2, max_digits=20)),
                ('disco_used', models.DecimalField(decimal_places=2, max_digits=20)),
                ('porcentagem_disco_used', models.DecimalField(decimal_places=0, max_digits=20)),
                ('path', models.CharField(blank=True, max_length=255, null=True)),
                ('node', models.CharField(blank=True, max_length=255, null=True)),
                ('aggregate', models.CharField(blank=True, max_length=255, null=True)),
                ('export_policy', models.CharField(blank=True, max_length=255, null=True)),
                ('deduplication', models.DecimalField(decimal_places=2, max_digits=20, null=True, verbose_name='Snap')),
                ('porcentagem_deduplication', models.CharField(blank=True, max_length=255, null=True)),
                ('svm_name', models.CharField(blank=True, max_length=255, null=True)),
                ('storage_grupo_trabalho', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='infra.StorageAreaGrupoTrabalho')),
            ],
        ),
    ]
