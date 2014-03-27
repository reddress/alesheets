from datetime import datetime
from django.db import models

# Create your models here.
class Owner(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=20)
    def __unicode__(self):
        return self.short_name
    def __str__(self):
        return self.__unicode__()

# start with Assets, Expense = Liability, Equity, Income
class AccountType(models.Model):
    name = models.CharField(max_length=40)
    sign_modifier = models.IntegerField(default=1)
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

class Account(models.Model):
    owner = models.ForeignKey(Owner)
    name = models.CharField(max_length=80)
    short_name = models.CharField(max_length=20)
    type = models.ForeignKey(AccountType)
    def __unicode__(self):
        return self.short_name
    def __str__(self):
        return self.__unicode__()

class Transaction(models.Model):
    description = models.CharField(max_length=80)
    date = models.DateTimeField(default=datetime.now)
    value = models.DecimalField(max_digits=14, decimal_places=2)
    debit = models.ForeignKey(Account, related_name="+")
    credit = models.ForeignKey(Account, related_name="+")
    def __unicode__(self):
        return "%s/%s/%s %s %s" % (self.date.day, self.date.month,
                                   self.date.year,
                                   self.description[:80], self.value)
    def __str__(self):
        return self.__unicode__()
