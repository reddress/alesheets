from django.contrib import admin
from .models import Owner, AccountType, Account, Transaction
# Register your models here.

class TransactionAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'debit' or db_field.name == 'credit':
            kwargs["queryset"] = Account.objects.order_by('short_name')
        return super(TransactionAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

admin.site.register(Owner)
admin.site.register(AccountType)
admin.site.register(Account)
admin.site.register(Transaction, TransactionAdmin)
