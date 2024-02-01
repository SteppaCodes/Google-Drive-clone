
import os
from decouple import config

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'google_drive_clone.settings.{config("SETTINGS")}')

application = get_asgi_application()
