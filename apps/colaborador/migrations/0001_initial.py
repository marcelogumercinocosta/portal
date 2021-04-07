# Generated by Django 3.0.8 on 2021-04-06 21:21

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Colaborador',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('telefone', models.CharField(max_length=255, verbose_name='telefone')),
                ('data_nascimento', models.DateField(max_length=255, verbose_name='Data de Nascimento')),
                ('documento', models.CharField(max_length=255, verbose_name='Documento')),
                ('documento_tipo', models.CharField(max_length=255, verbose_name='Tipo Documento')),
                ('cpf', models.CharField(blank=True, max_length=255, null=True, verbose_name='CPF')),
                ('data_inicio', models.DateField(verbose_name='Data de Início')),
                ('data_fim', models.DateField(blank=True, null=True, verbose_name='Data de Fim')),
                ('ramal', models.CharField(blank=True, max_length=255, null=True, verbose_name='Ramal')),
                ('empresa', models.CharField(blank=True, max_length=255, null=True, verbose_name='Empresa Terceirizada')),
                ('registro_inpe', models.CharField(blank=True, max_length=255, null=True, verbose_name='Matrícula SIAPE')),
                ('externo', models.BooleanField(default=False, verbose_name='Usuário Externo')),
                ('uid', models.IntegerField(default=0, verbose_name='UID')),
                ('is_active', models.BooleanField(default=False, verbose_name='ativo')),
            ],
            options={
                'verbose_name': 'Colaborador',
                'verbose_name_plural': 'Colaboradores',
                'ordering': ['username'],
                'permissions': (('responsavel_colaborador', 'Responsável pode aprovar acesso colaborador'), ('secretaria_colaborador', 'Secretaria pode revisar colaborador'), ('suporte_colaborador', 'Suporte pode criar o colaborador'), ('chefia_colaborador', 'Chefia por aprovar colaborador')),
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Vinculo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vinculo', models.CharField(max_length=255, verbose_name='vínculo')),
            ],
            options={
                'verbose_name': 'Vínculo',
                'verbose_name_plural': 'Vínculos',
                'ordering': ['vinculo'],
            },
        ),
        migrations.CreateModel(
            name='VPN',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recurso', models.CharField(max_length=255, verbose_name='Recurso a ser acessado')),
                ('data_solicitacao', models.DateField(auto_now_add=True, verbose_name='Data da solicitação')),
                ('data_abertura', models.DateField(blank=True, null=True, verbose_name='Data da Abertura')),
                ('data_validade', models.DateField(blank=True, null=True, verbose_name='Data Validade')),
                ('mac_cabeado', models.CharField(blank=True, max_length=255, null=True, verbose_name='MAC Address Cabeado')),
                ('mac_wifi', models.CharField(blank=True, max_length=255, null=True, verbose_name='MAC Address Wireless')),
                ('justificativa', models.CharField(max_length=255, verbose_name='Justificativa')),
                ('status', models.CharField(blank=True, default='Solicitada', max_length=255, null=True, verbose_name='Status')),
                ('colaborador', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Colaborador')),
            ],
            options={
                'verbose_name': 'VPN',
                'verbose_name_plural': 'VPNs',
                'ordering': ['-data_validade'],
            },
        ),
    ]
