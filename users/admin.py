from django.contrib.auth.models import User
from django.db import models
from tastypie.models import create_api_key
from users.models import Project, GopherAirtimeAccount
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


models.signals.post_save.connect(create_api_key, sender=User)


class ProjectAdmin(admin.ModelAdmin):
    pass


class GopherAirtimeAccountAdmin(admin.ModelAdmin):
    pass


admin.site.register(Project, ProjectAdmin)
admin.site.register(GopherAirtimeAccount, GopherAirtimeAccountAdmin)
