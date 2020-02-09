from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'howsmytrack.core'

    def ready(self):
        print('core app ready')
