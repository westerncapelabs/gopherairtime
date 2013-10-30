from django.contrib import admin
from recharge.models import Recharge, RechargeError, RechargeFailed


class RechargeAdmin(admin.ModelAdmin):
    list_display = ["id", "msisdn", "reference", "status", "recharge_system_ref", "notification","status_confirmed_at"]


class RechargeErrorAdmin(admin.ModelAdmin):
    list_display = ["recharge_error", "error_id", "error_message", "tries", "last_attempt_at"]


class RechargeFailedAdmin(admin.ModelAdmin):
    list_display = ["recharge_failed", "recharge_status", "failure_message"]


admin.site.register(Recharge, RechargeAdmin)
admin.site.register(RechargeError, RechargeErrorAdmin)
admin.site.register(RechargeFailed, RechargeFailedAdmin)
