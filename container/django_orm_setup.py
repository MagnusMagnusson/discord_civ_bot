import django
from django.conf import settings
from civboard.settings import DATABASES
from civboard.settings import INSTALLED_APPS

settings.configure(
    DATABASES=DATABASES,
    INSTALLED_APPS=INSTALLED_APPS
)

django.setup()