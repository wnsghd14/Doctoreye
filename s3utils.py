from django.conf import settings as django_settings
from storages.backends.s3 import S3Storage


class StaticRootS3BotoStorage(S3Storage):

    def __init__(self, **settings):
        settings['custom_domain'] = django_settings.ASSETS_HOST_URL
        settings['location'] = 'static'
        super(StaticRootS3BotoStorage, self).__init__(**settings)
        pass


class MediaRootS3BotoStorage(S3Storage):

    def __init__(self, **settings):
        settings['custom_domain'] = django_settings.ASSETS_HOST_URL
        settings['location'] = 'media'
        super(MediaRootS3BotoStorage, self).__init__(**settings)
        pass
