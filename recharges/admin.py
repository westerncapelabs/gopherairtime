from django.contrib import admin

from recharges.models import Recharge, Account


class RechargeAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'amount', 'reference', 'hotsocket_ref',
                    'status', 'status_message', 'network_code',
                    'product_code', 'created_at', 'updated_at')
    list_filter = ['status', 'network_code',
                   'product_code', 'created_at', 'updated_at']
    search_fields = ['msisdn', 'reference', 'hotsocket_ref',
                     'status_message']


class AccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'token', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['id', 'token']


admin.site.register(Recharge, RechargeAdmin)
admin.site.register(Account, AccountAdmin)
