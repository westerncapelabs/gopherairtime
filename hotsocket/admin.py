from django.contrib import admin
from hotsocket.models import Recharge, RechargeError


class RehcargeAdmin(admin.ModelAdmin):
    pass


class RechargeErrorAdmin(admin.ModelAdmin):
    pass

admin.site.register(Recharge, RehcargeAdmin)
admin.site.register(RechargeError, RechargeErrorAdmin)