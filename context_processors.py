from django.conf import settings


def env(request):
    return {
        'APP_ENV': settings.APP_ENV,
    }
