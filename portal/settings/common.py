import os
import environ

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__ + "/../")))


environment = {'portal.settings.development':"dev.env", 'portal.settings.test':"test.env", 'portal.settings.production':"prod.env" }
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, environment[os.environ.get('django_settings_module')]))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY') 

# Application definition

INSTALLED_APPS = [
    "garb",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "freeipa",
    "celery",
    "celery_progress",
    "django_cleanup.apps.CleanupConfig",
    "apps.core",
    "apps.colaborador",
    "apps.infra",
    "apps.monitoramento",
    "apps.biblioteca",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages",'django.template.context_processors.media',],},
    },
]

WSGI_APPLICATION = "portal.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

AUTH_USER_MODEL = 'colaborador.Colaborador'

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = "/staticfiles/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

MEDIA_URL = "/media/"


GARB_CONFIG = {
    "PROJECT_NAME": "3SPortal",
    "ROUTE_PROFILE": "colaborador:conta",
    "NAME_PROFILE": "CONTA",
    "ADMIN_ACTIONS_ALL": False,
    "ADMIN_WIDGET_CAN": False,
    "THEME": "hybrid",
    "LIST_PER_PAGE": 15,
    "MENU": [
        {"label": "Novo Colaborador", "icon": "fa-user-plus", "route": "colaborador_open:inicio", "auth": "no"},
        {"label": "Estrutura de Grupos", "icon": "fa-user-friends", "route": "core_open:grupos", "auth": "all"},
        {
            "label": "Colaborador",
            "icon": "fa-handshake",
            "sub_itens": [
                {"model": "colaborador.colaborador"},
                {"label": "Secretaria", "permission": "colaborador.secretaria_colaborador", "route": "colaborador:secretaria",},
                {"label": "Suporte", "permission": "colaborador.suporte_colaborador", "route": "colaborador:suporte",},
                {"label": "Responsável", "permission": "colaborador.responsavel_colaborador", "route": "colaborador:responsavel",},
                {"model": "colaborador.vpn"},
                {"model": "colaborador.vinculo"},
                {"model": "core.divisao"},
            ],
        },
        {"label": "Administrador", "icon": "fa-user-cog", "sub_itens": [{"model": "core.grupotrabalho"}, {"model": "core.grupoacesso"}, {"model": "core.grupoportal"}]},
        
        {
            "label": "Infraestrutura",
            "icon": "fa-building",
            "sub_itens": [
                {"label": "Datacenter", "route": "infra:datacenter", "auth": "all"},
                {"model": "infra.servidor"},
                {"model": "infra.storage"},
                {"model": "infra.supercomputador"},
                {"model": "infra.equipamentoparte"},
                {"model": "infra.ambientevirtual"},
                {"model": "infra.templatevm"},
                {"model": "infra.rack"},
                {"model": "infra.hostnameip"},
            ],
        },
        {
            "label": "Monitoramento",
            "icon": "fa-chart-line",
            "sub_itens": [
                {"label": "Supercomputador Jobs e Nodes", "route": "monitoramento:uso_supercomputador", "auth": "all"},
                {"label": "Armazenamento", "route": "monitoramento:storage_netapp", "auth": "all"},
                {"label": "Ambiente Virtual", "route": "monitoramento:vms_xen", "auth": "all"},
                {"label": "Ferramentas", "route": "monitoramento:ferramentas", "auth": "all"},
                {"label": "RNP", "route": "monitoramento:rnp_home", "auth": "all"},
                {"model": "monitoramento.tipomonitoramento"},
            ],
        },
        {
            "label": "Biblioteca",
            "icon": "fa-book",
            "sub_itens": [
                {"model": "biblioteca.documento"},
                {"label": "Listar Documentos", "route": "biblioteca:documentos", "auth": "all"},
            ],
        },
    ],
}

LOGIN_URL = '/conta/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = env('EMAIL_HOST_USER') 
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD') 
EMAIL_PORT = 587
EMAIL_SUPORTE = env('EMAIL_SUPORTE') 
EMAIL_SYSADMIN = env('EMAIL_SYSADMIN')

#celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_TIME_LIMIT = 5 * 60
CELERY_TASK_SOFT_TIME_LIMIT =  5 * 60
CELERY_RESULT_EXPIRES = 5 * 60
CELERY_TIMEZONE = "UTC"
CELERY_TRACK_STARTED = True
CELERY_ACKS_LATE = True 

#servers
SERVERS_ROOT = env('SERVERS_ROOT')
SERVERS_PASSWORD = env('SERVERS_PASSWORD')

# freeipa
# REQUIRED:
IPA_AUTH_SERVER = env('IPA_AUTH_SERVER')
IPA_AUTH_USER =  env('IPA_AUTH_USER')
IPA_AUTH_PASSWORD = env('IPA_AUTH_PASSWORD')

# OPTIONAL:
IPA_AUTH_SERVER_SSL_VERIFY = BASE_DIR + env('IPA_AUTH_FILE')
IPA_AUTH_SERVER_API_VERSION = "2.229"
# Automatically update user information when logged in
IPA_AUTH_AUTO_UPDATE_USER_INFO = False
# Automatically create and update user groups.
IPA_AUTH_UPDATE_USER_GROUPS = False
# Dictionary mapping FreeIPA field to Django user attributes
IPA_AUTH_FIELDS_MAP = {"password": "password"}

# KAFKA
KAFKA_SERVER = env('KAFKA_SERVER') 

# XEN
XEN_AUTH_USER = env('XEN_AUTH_USER') 
XEN_AUTH_PASSWORD = env('XEN_AUTH_PASSWORD') 

# MQTT
MOSQUITTO_SERVER = env('MOSQUITTO_SERVER') 
MOSQUITTO_PORT = env('MOSQUITTO_PORT') 