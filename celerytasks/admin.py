from django.contrib import admin
from celerytasks.models import StoreToken

class StoreTokenAdmin(admin.ModelAdmin):
    list_display = ["token", "updated_at", "expire_at"]


admin.site.register(StoreToken, StoreTokenAdmin)
