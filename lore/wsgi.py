import os
from decouple import config

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'lore.settings.{config("SETTINGS")}')

application = get_wsgi_application()
