from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "howsmytrack.core"

    def ready(self):
        print("Core app ready.")
