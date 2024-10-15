import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_project.settings")  # Replace with your project's settings module

app = get_wsgi_application()
