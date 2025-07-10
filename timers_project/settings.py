from pathlib import Path
from decouple import config, Csv
import colorlog
import time
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

INSTALLED_APPS = [
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'timers_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'timers_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'timers_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'nl-nl'
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

LOG_LEVEL = config('LOG_LEVEL', default='INFO')
LOG_FILENAME = f'dynamic-timers-{time.strftime("%m-%d-%Y")}.log'

active_handlers = ['console']
if LOG_LEVEL == 'DEBUG':
    active_handlers.append('debug_file')
else:
    active_handlers.append('info_rotating_file')

log_dir = BASE_DIR / "logs"
log_dir.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        },
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_white,bg_red',
            },
        },
        'extended': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s - [%(pathname)s - %(module)s - %(funcName)s - %(lineno)d]',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'formatter': 'colored',
            'class': 'logging.StreamHandler',
        },
        'debug_file': {
            'level': 'DEBUG',
            'formatter': 'extended',
            'class': 'logging.FileHandler',
            'filename': os.path.join(log_dir, ('debug-' + LOG_FILENAME)),
            'mode': 'a',
        },
        'info_rotating_file': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(log_dir, LOG_FILENAME),
            'maxBytes': 10485760,
            'backupCount': 31,
        },
    },
    'loggers': {
        'django': {
            'handlers': active_handlers,
            'level': LOG_LEVEL,
            'propagate': True,
        },
    },
}
