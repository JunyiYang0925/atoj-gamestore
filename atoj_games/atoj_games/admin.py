from django.contrib import admin
from atoj_games.models import *
from django.apps import apps

# To enable Django's admin panel uncomment admin-url in urls.py.

# Imports all atoj_games models
for model in apps.get_app_config('atoj_games').models.values():
    admin.site.register(model)
