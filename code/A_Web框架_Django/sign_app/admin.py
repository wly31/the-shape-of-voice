from django.contrib import admin
from .models import SignHistory, ActivityLog

admin.site.register(SignHistory)
admin.site.register(ActivityLog)
