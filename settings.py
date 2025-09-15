from pathlib import Path
import os
import environ
import json
import boto3
from botocore.exceptions import ClientError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

APP_ENV = os.environ.get('APP_ENV')
APP_ROLE = os.environ.get('APP_ROLE')

GENERAL_SECRET_NAME = os.environ.get('GENERAL_ENV')
THIRD_PARTY_SECRET_NAME = os.environ.get('THIRD_PARTY_ENV')
AWS_REGION_NAME = os.environ.get('AWS_REGION')

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError


def get_secret(name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=AWS_REGION_NAME
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=name)
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']

    return json.loads(secret)


if APP_ENV not in ['DEVELOP', 'PRODUCTION', 'QA', 'STAGING']:
    # It means in LocalServer
    ENV_GENERAL = os.environ
    ENV_THIRD_PARTY = os.environ
    RDS_SECRETS_NAME = None
    GENERAL_SECRET_NAME = ENV_GENERAL.get('GENERAL_ENV')
    THIRD_PARTY_SECRET_NAME = ENV_GENERAL.get('THIRD_PARTY_ENV')
    AWS_REGION_NAME = ENV_GENERAL.get('AWS_REGION')
    DEBUG = True
    # SESSION_COOKIE_AGE = 10  # 10초 유지
else:
    SECRETS_ENV = get_secret(GENERAL_SECRET_NAME)
    DEBUG = False
    # SECRETS_ENV_THIRD_PARTY = get_secret(THIRD_PARTY_SECRET_NAME)
    # RDS_SECRETS_NAME = SECRETS_ENV.get('RDS_SECRETS_NAME')

    # for s3 static / media files
    ASSETS_HOST_URL = SECRETS_ENV.get('ASSETS_HOST_URL')
    AWS_STORAGE_BUCKET_NAME = SECRETS_ENV.get('AWS_STORAGE_BUCKET_NAME')
    DEFAULT_FILE_STORAGE = 'config.s3utils.MediaRootS3BotoStorage'
    STATICFILES_STORAGE = 'config.s3utils.StaticRootS3BotoStorage'
    AWS_ACCESS_KEY_ID = SECRETS_ENV.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = SECRETS_ENV.get('AWS_SECRET_ACCESS_KEY')

    MASTER_PASSWORD = SECRETS_ENV.get('MASTER_PASSWORD')
    # 세션 자동 종료 시각 설정 코드
    SESSION_COOKIE_AGE = 86400
    SECURE_SSL_REDIRECT = SECRETS_ENV.get("SECURE_SSL_REDIRECT")
    SECURE_REDIRECT_EXEMPT = [
        '/health',  # HTTPS 리디렉션 예외 URL
    ]
    SESSION_COOKIE_SECURE = SECRETS_ENV.get('SESSION_COOKIE_SECURE')
    CSRF_COOKIE_SECURE = SECRETS_ENV.get('CSRF_COOKIE_SECURE')
    CSRF_COOKIE_AGE = 86400
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # SECURE_BROWSER_XSS_FILTER = SECRETS_ENV.get('SECURE_BROWSER_XSS_FILTER')
    # X_FRAME_OPTIONS = SECRETS_ENV.get('X_FRAME_OPTIONS')
    # X_CONTENT_TYPE_OPTIONS = SECRETS_ENV.get('X_CONTENT_TYPE_OPTIONS')
    # SECURE_REFERRER_POLICY = SECRETS_ENV.get('SECURE_REFERRER_POLICY')
    # SECURE_HSTS_SECONDS = SECRETS_ENV.get('SECURE_HSTS_SECONDS')
    # ENV_THIRD_PARTY = SECRETS_ENV_THIRD_PARTY
    ENV_GENERAL = SECRETS_ENV

if APP_ENV == 'PRODUCTION':
    # For Production Page domain
    CSRF_TRUSTED_ORIGINS = [
        'https://doctoreye.kr/', 'https://www.doctoreye.kr/'
    ]
    CORS_ALLOWED_ORIGINS = [
        'https://doctoreye.kr/', 'https://www.doctoreye.kr/'
    ]

elif APP_ENV == 'LOCAL':
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000/', 'http://localhost:8001'
    ]
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:8000/', 'http://localhost:8001'
    ]
else:
    CSRF_TRUSTED_ORIGINS = []
    CORS_ALLOWED_ORIGINS = []

# These things are not going to be changed

SECRET_KEY = ENV_GENERAL.get('SECRET_KEY')
MASTER_EMAIL = ENV_GENERAL.get('MASTER_EMAIL')
MASTER_NAME = ENV_GENERAL.get('MASTER_NAME')
MASTER_PASSWORD = ENV_GENERAL.get('MASTER_PASSWORD')
EMAIL_BACKEND = ENV_GENERAL.get('EMAIL_BACKEND')
EMAIL_HOST = ENV_GENERAL.get('EMAIL_HOST')
EMAIL_PORT = ENV_GENERAL.get('EMAIL_PORT')
EMAIL_HOST_USER = ENV_GENERAL.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = ENV_GENERAL.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = ENV_GENERAL.get('EMAIL_USE_SSL')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ALLOWED_HOSTS = ["*"]
MODEL_PATH = ENV_GENERAL.get('MODEL_PATH')
UPLOAD_URL = ENV_GENERAL.get('UPLOAD_URL')
CLASSIFY_URL = ENV_GENERAL.get('CLASSIFY_URL')


FIELD_ENCRYPTION_KEY_1 = ENV_GENERAL.get('FIELD_ENCRYPTION_KEY')

FIELD_ENCRYPTION_KEYS = [
    FIELD_ENCRYPTION_KEY_1,
]

ENC_FIELD_KEY = FIELD_ENCRYPTION_KEYS[0]

# To manage featured apps
FEATURED_APPS = [
    'users.apps.UsersConfig',
    'doctors.apps.DoctorsConfig',
    'core.apps.CoreConfig',
]

# To manage pip apps
PIP_LIBS = [
    # Encrypting dataset
    'encrypted_fields',
    'environ',
    'import_export',
    'rest_framework',
]

INSTALLED_APPS = FEATURED_APPS + PIP_LIBS + [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework.authtoken',
    
]

# To manage custom middleware
SELF_MADE_MIDDLEWARE = [
    'core.middlewares.HealthCheckMiddleware',
    'core.middlewares.RequestLoggerMiddleware',
    'core.middlewares.RedirectAllErrorsMiddleware',
    # 'core.middlewares.IPWhitelistMiddleware',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]+ SELF_MADE_MIDDLEWARE

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.env',
            ],
            'libraries': {
                'template_tags': 'core.template_tags',
            }
        },
    },
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases


DB_NAME = ENV_GENERAL.get('DB_NAME')
DB_USER = ENV_GENERAL.get('DB_USER')
DB_HOST = ENV_GENERAL.get('DB_HOST')
DB_PASSWORD = ENV_GENERAL.get('DB_PASSWORD')
DB_ENGINE = ENV_GENERAL.get('DB_ENGINE')
DB_PORT = ENV_GENERAL.get('DB_PORT')

DATABASES = {
    'default': {
        'ENGINE': DB_ENGINE,
        'NAME': DB_NAME,
        'USER': DB_USER,
        'HOST': DB_HOST,
        'PASSWORD': DB_PASSWORD,
    },
    # For multiple Database setting if needed
    # 'users': {
    #
    # },
    # 'patients': {
    #
    # }
}

APPEND_SLASH = False

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Allow file uploads up to 20MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]
AUTH_USER_MODEL = 'users.User'

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

