from django.contrib import admin
from recharge.models import Recharge, RechargeError


class RechargeAdmin(admin.ModelAdmin):
    pass


class RechargeErrorAdmin(admin.ModelAdmin):
    pass

admin.site.register(Recharge, RechargeAdmin)
admin.site.register(RechargeError, RechargeErrorAdmin)
