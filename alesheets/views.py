from itertools import chain
from datetime import datetime, timedelta

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import Owner, AccountType, Account, Transaction

@login_required
def index(request):
    asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
    expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
    liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
    equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
    income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')

    return render(request, 'alesheets/index.html',
                  {'asset_accounts': asset_accounts,
                   'expense_accounts': expense_accounts,
                   'liability_accounts': liability_accounts,
                   'equity_accounts': equity_accounts,
                   'income_accounts': income_accounts})

def get_transaction_html(transaction, account, balance):
    sign = account.type.sign_modifier
    if str(transaction.credit) == str(account.short_name):
        sign *= -1
        
    new_balance = balance + (sign * transaction.value)

    wkdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    table_row = """<tr>
    <td><a href="/admin/alesheets/transaction/%s/" target="alesheets_admin">
          %s</a</td>
    <td>%s %s/%s/%s %02d:%02d</td> <!-- Date -->
    <td>%s</td> <!-- Description -->""" % (transaction.id,
                                           transaction.id,
                                           wkdays[transaction.date.weekday()],
                                           transaction.date.day,
                                           transaction.date.month,
                                           transaction.date.year,
                                           transaction.date.hour,
                                           transaction.date.minute,
                                           transaction.description)

    if str(transaction.debit) == str(account.short_name):
        table_row += '''
        <td>%.2f</td>
        <td><a href="../%s">%s</a></td>''' % (transaction.value,
                                              transaction.credit,
                                              transaction.credit)
    else:
        table_row += '''
        <td><a href="../%s">%s</a></td>
        <td>%.2f</td>
        ''' % (transaction.debit, transaction.debit, transaction.value)

    table_row += '<td>%.2f</td></tr>' % new_balance
    
    return (table_row, new_balance)

@login_required
def show_category(request, category_name, days_back):
    asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
    expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
    liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
    equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
    income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')

    raw_transactions = Transaction.objects.filter(Q(debit__type__name=category_name),
        date__gte=(datetime.today() - timedelta(days=int(days_back))))
    sorted_transactions = list(reversed(sorted(raw_transactions, key=lambda tr: tr.date)))
    total = sum([tr.value for tr in sorted_transactions])

    daily_totals = {}
    
    for tr in sorted_transactions:
        short_date = "%s-%02d-%02d" % (tr.date.year, tr.date.month, tr.date.day)
        if short_date not in daily_totals:
            daily_totals[short_date] = tr.value
        else:
            daily_totals[short_date] += tr.value

    # set nonexistent days to 0.00 (decimal places formatted in template)
    today = datetime.today()
    for day in range(int(days_back)):
        formatted_day = (today - timedelta(days=day)).strftime("%Y-%m-%d")
        if formatted_day not in daily_totals:
            daily_totals[formatted_day] = 0

    def rearrange_date(date_string):
        return datetime.strptime(date_string, "%Y-%m-%d").strftime("%d/%m/%Y %a")
    daily_totals_pair = []
    for day in reversed(sorted(daily_totals)):
        daily_totals_pair.append((rearrange_date(day), daily_totals[day]))

    credit_transactions = Transaction.objects.filter(credit__type__name=category_name)
    
    
    return render(request, 'alesheets/showcategory.html',
                  {'account_name': category_name,
                   'account_short_name': category_name,
                   'transactions': sorted_transactions,
                   'credit_transactions': credit_transactions,
                   'asset_accounts': asset_accounts,
                   'expense_accounts': expense_accounts,
                   'liability_accounts': liability_accounts,
                   'equity_accounts': equity_accounts,
                   'income_accounts': income_accounts,
                   'last_balance': "0.00",
                   'balance_change': "0.00",
                   'total': total,
                   'daily_totals': daily_totals_pair,
                   'report_type': "Transactions in the last %d days" % int(days_back), })
    
@login_required
def show_account(request, short_name):
    asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
    expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
    liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
    equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
    income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')
    
    account = get_object_or_404(Account, short_name=short_name)
    last_balance = get_balance_not_shown(account)
    
    debit_transactions = Transaction.objects.filter(debit=account,
                            date__gte=(datetime.today()-timedelta(days=31)))
    credit_transactions = Transaction.objects.filter(credit=account,
                            date__gte=(datetime.today()-timedelta(days=31)))
    raw_transactions = sorted(chain(debit_transactions,
                                    credit_transactions),
                              key=lambda tr: tr.date)
    all_transactions = []
    balance = get_balance_not_shown(account)

    for transaction in raw_transactions:
        row_data = get_transaction_html(transaction, account, balance)
        all_transactions.append(row_data[0])
        balance = row_data[1]

    balance_change = balance - last_balance
        
    return render(request, 'alesheets/showaccount.html',
                  {'account_name': account.name,
                   'account_short_name': account.short_name,
                   'transactions': all_transactions,
                   'asset_accounts': asset_accounts,
                   'expense_accounts': expense_accounts,
                   'liability_accounts': liability_accounts,
                   'equity_accounts': equity_accounts,
                   'income_accounts': income_accounts,
                   'last_balance': "%.2f" % last_balance,
                   'balance_change': "%.2f" % balance_change,
                   'report_type': "Last 31 days", })

@login_required
def show_account_custom_date(request, short_name, start_year, start_month,
                             start_day, end_year, end_month, end_day):
    start_year = int(start_year)
    start_month = int(start_month)
    start_day = int(start_day)
    end_year = int(end_year)
    end_month = int(end_month)
    end_day = int(end_day)
    start_date = datetime(start_year, start_month, start_day, 0, 0)
    end_date = datetime(end_year, end_month, end_day, 23, 59)
    
    asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
    expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
    liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
    equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
    income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')
    
    account = get_object_or_404(Account, short_name=short_name)
    # set to zero, or else must alter get_bal_not_shown function
    last_balance = 0
    
    debit_transactions = Transaction.objects.filter(debit=account,
                            date__gt=start_date, date__lt=end_date)
    credit_transactions = Transaction.objects.filter(credit=account,
                            date__gt=start_date, date__lt=end_date)
    raw_transactions = sorted(chain(debit_transactions,
                                    credit_transactions),
                              key=lambda tr: tr.date)
    all_transactions = []
    balance = 0

    for transaction in raw_transactions:
        row_data = get_transaction_html(transaction, account, balance)
        all_transactions.append(row_data[0])
        balance = row_data[1]

    balance_change = balance - last_balance
        
    return render(request, 'alesheets/showaccount.html',
                  {'account_name': account.name,
                   'account_short_name': account.short_name,
                   'transactions': all_transactions,
                   'asset_accounts': asset_accounts,
                   'expense_accounts': expense_accounts,
                   'liability_accounts': liability_accounts,
                   'equity_accounts': equity_accounts,
                   'income_accounts': income_accounts,
                   'last_balance': "%.2f" % last_balance,
                   'balance_change': "%.2f" % balance_change,
                   'report_type': "Custom dates",
                   'start_date': start_date,
               })
    
@login_required
def show_account_all(request, short_name):
    asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
    expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
    liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
    equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
    income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')
    
    account = get_object_or_404(Account, short_name=short_name)
    last_balance = 0
    
    debit_transactions = Transaction.objects.filter(debit=account)
    credit_transactions = Transaction.objects.filter(credit=account)
    raw_transactions = sorted(chain(debit_transactions,
                                    credit_transactions),
                              key=lambda tr: tr.date)
    all_transactions = []
    balance = 0

    for transaction in raw_transactions:
        row_data = get_transaction_html(transaction, account, balance)
        all_transactions.append(row_data[0])
        balance = row_data[1]

    balance_change = balance - last_balance
        
    return render(request, 'alesheets/showaccount.html',
                  {'account_name': account.name,
                   'account_short_name': account.short_name,
                   'transactions': all_transactions,
                   'asset_accounts': asset_accounts,
                   'expense_accounts': expense_accounts,
                   'liability_accounts': liability_accounts,
                   'equity_accounts': equity_accounts,
                   'income_accounts': income_accounts,
                   'last_balance': "%.2f" % last_balance,
                   'balance_change': "%.2f" % balance_change,
                   'report_type': "All transactions", })

# def get_balance_html(account):
#     balance = 0
    
#     debit_transactions = Transaction.objects.select_related('debit').filter(debit=account)
#     credit_transactions = Transaction.objects.select_related('credit').filter(credit=account)
#     #raw_transactions = sorted(chain(debit_transactions,
#     #                                credit_transactions),
#     #                          key=lambda tr: tr.date)
#     raw_transactions = chain(debit_transactions, credit_transactions)
    
#     for transaction in raw_transactions:
#         sign = account.type.sign_modifier
#         if str(transaction.credit) == str(account.short_name):
#             sign *= -1
#         balance += sign * transaction.value
#     return '<tr><td><a href="/alesheets/account/%s/">%s</a></td><td align="right">%.2f</td></tr>' % (account.short_name, account.short_name, balance)

# def get_balance_value(account):
#     balance = 0

#     debit_transactions = Transaction.objects.select_related('debit').filter(debit=account)
#     credit_transactions = Transaction.objects.select_related('credit').filter(credit=account)
#     #raw_transactions = sorted(chain(debit_transactions,
#     #                                credit_transactions),
#     #                          key=lambda tr: tr.date)
#     raw_transactions = chain(debit_transactions, credit_transactions)
    
#     for transaction in raw_transactions:
#         sign = account.type.sign_modifier
#         if str(transaction.credit) == str(account.short_name):
#             sign *= -1
#         balance += sign * transaction.value
#     return balance

# def get_balance_html_latest(account, days_back):
#     balance = 0
#     debit_transactions = Transaction.objects.filter(debit=account,
#                     date__gte=(datetime.today()-timedelta(days=days_back)))

#     credit_transactions = Transaction.objects.filter(credit=account,
#                     date__gte=(datetime.today()-timedelta(days=days_back)))
#     #raw_transactions = sorted(chain(debit_transactions,
#     #                                credit_transactions),
#     #                          key=lambda tr: tr.date)
#     raw_transactions = chain(debit_transactions, credit_transactions)
    
#     for transaction in raw_transactions:
#         sign = account.type.sign_modifier
#         if str(transaction.credit) == str(account.short_name):
#             sign *= -1
#         balance += sign * transaction.value
#     return '<tr><td><a href="/alesheets/account/%s/">%s</a></td><td align="right">%.2f</td></tr>' % (account.short_name, account.short_name, balance)

# def get_balance_value_latest(account, days_back):
#     balance = 0

#     debit_transactions = Transaction.objects.filter(debit=account,
#                         date__gte=(datetime.today()-timedelta(days=days_back)))
#     credit_transactions = Transaction.objects.filter(credit=account,
#                         date__gte=(datetime.today()-timedelta(days=days_back)))
#     #raw_transactions = sorted(chain(debit_transactions,
#     #                                credit_transactions),
#     #                          key=lambda tr: tr.date)
#     raw_transactions = chain(debit_transactions, credit_transactions)
        
#     for transaction in raw_transactions:
#         sign = account.type.sign_modifier
#         if str(transaction.credit) == str(account.short_name):
#             sign *= -1
#         balance += sign * transaction.value
#     return balance

def get_balance_not_shown(account):
    balance = 0
    debit_transactions = Transaction.objects.filter(debit=account,
                            date__lt=(datetime.today()-timedelta(days=31)))
    credit_transactions = Transaction.objects.filter(credit=account,
                            date__lt=(datetime.today()-timedelta(days=31)))               
    #raw_transactions = sorted(chain(debit_transactions,
    #                                credit_transactions),
    #                          key=lambda tr: tr.date)
    raw_transactions = chain(debit_transactions, credit_transactions)
    
    for transaction in raw_transactions:
        sign = account.type.sign_modifier
        if str(transaction.credit) == str(account.short_name):
            sign *= -1
        balance += sign * transaction.value
    return balance

# @login_required
# def show_balances(request):
#     asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
#     expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
#     liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
#     equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
#     income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')

#     account_types = [asset_accounts, expense_accounts, liability_accounts,
#                      equity_accounts, income_accounts]
#     type_balances = []
#     type_totals = []
#     for type in account_types:
#         # map get_balance for all accounts in asset_accounts,
#         # expense_accounts, etc. then place it in type_balances
#         type_balances.append(map(get_balance_html, type))
#         type_totals.append("%.2f" % sum(map(get_balance_value, type)))
        
#     return render(request, 'alesheets/showbalances.html',
#                   {'type_balances': type_balances,
#                    'type_totals': type_totals,
#                    'asset_accounts': asset_accounts,
#                    'expense_accounts': expense_accounts,
#                    'liability_accounts': liability_accounts,
#                    'equity_accounts': equity_accounts,
#                    'income_accounts': income_accounts,
#                    'report_type': "All transactions", })

# @login_required
# def balance_changes(request, days_back):
#     asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
#     expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
#     liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
#     equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
#     income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')

#     account_types = [asset_accounts, expense_accounts, liability_accounts,
#                      equity_accounts, income_accounts]
#     type_balances = []
#     type_totals = []

#     def get_balance_html_wrapper(x):
#         return get_balance_html_latest(x, int(days_back))

#     def get_balance_value_wrapper(x):
#         return get_balance_value_latest(x, int(days_back))
    
#     for type in account_types:
#         # map get_balance for all accounts in asset_accounts,
#         # expense_accounts, etc. then place it in type_balances
#         type_balances.append(map(get_balance_html_wrapper, type))
#         type_totals.append("%.2f" % sum(map(get_balance_value_wrapper, type)))
        
#     return render(request, 'alesheets/showbalances.html',
#                   {'type_balances': type_balances,
#                    'type_totals': type_totals,
#                    'asset_accounts': asset_accounts,
#                    'expense_accounts': expense_accounts,
#                    'liability_accounts': liability_accounts,
#                    'equity_accounts': equity_accounts,
#                    'income_accounts': income_accounts,
#                    'report_type': "Transactions in the last " + days_back + " days", })

@login_required
def search_transactions(request, keyword):
    asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
    expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
    liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
    equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
    income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')

    transactions = Transaction.objects.filter(description__icontains=keyword).order_by('date').reverse()

    return render(request, 'alesheets/transaction_results.html',
                  {'asset_accounts': asset_accounts,
                   'expense_accounts': expense_accounts,
                   'liability_accounts': liability_accounts,
                   'equity_accounts': equity_accounts,
                   'income_accounts': income_accounts,
                   'transactions': transactions,})
@login_required
def search_none(request):
    asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
    expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
    liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
    equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
    income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')

    transactions = ["Enter search term on the address bar"]
    
    return render(request, 'alesheets/transaction_results.html',
                  {'asset_accounts': asset_accounts,
                   'expense_accounts': expense_accounts,
                   'liability_accounts': liability_accounts,
                   'equity_accounts': equity_accounts,
                   'income_accounts': income_accounts,
                   'transactions': transactions,})

@login_required
def compute_balances(request, days_back=-1):
    asset_accounts = Account.objects.filter(type__name="Asset").order_by('short_name')
    expense_accounts = Account.objects.filter(type__name="Expense").order_by('short_name')
    liability_accounts = Account.objects.filter(type__name="Liability").order_by('short_name')
    equity_accounts = Account.objects.filter(type__name="Equity").order_by('short_name')
    income_accounts = Account.objects.filter(type__name="Income").order_by('short_name')

    categories = {}
    balances = {}
    totals = {}

    category_objs = AccountType.objects.all()

    for category_obj in category_objs:
        categories[category_obj.name] = ""
        totals[category_obj.name] = 0
        
    account_objs = Account.objects.all()
    account_multiplier = {}
    account_category = {}
    for account_obj in account_objs:
        account_multiplier[account_obj.short_name] = account_obj.type.sign_modifier
        account_category[account_obj.short_name] = account_obj.type.name
        balances[account_obj.short_name] = 0

    if int(days_back) < 0:
        transactions = Transaction.objects.select_related('debit', 'credit').all()
    else:
        transactions = Transaction.objects.select_related('debit', 'credit').filter(date__gte=(datetime.today()-timedelta(days=int(days_back))))
        
    for transaction in transactions:
        debit_acct = transaction.debit.short_name
        credit_acct = transaction.credit.short_name

        balances[debit_acct] += transaction.value * account_multiplier[debit_acct]
        balances[credit_acct] -= transaction.value * account_multiplier[credit_acct]

    # result = []
    for acct in sorted(balances):
        acct_bal = "%.2f" % balances[acct]
        totals[account_category[acct]] += balances[acct]
        categories[account_category[acct]] += '<tr><td><a href="/alesheets/account/' + str(acct) + '/">' + str(acct) + '</a></td><td align="right">' + str(acct_bal) + "</td></tr>"
        # result.append(str(acct) + "??? " + account_category[acct] + str(balances[acct]))

    for category in totals:
        totals[category] = "%.2f" % totals[category]

    if int(days_back) < 0:
        days_back = "(all)"
    # print(categories)
    return render(request, 'alesheets/computedbal.html',
                  {'asset_accounts': asset_accounts,
                   'expense_accounts': expense_accounts,
                   'liability_accounts': liability_accounts,
                   'equity_accounts': equity_accounts,
                   'income_accounts': income_accounts,
                   'days_back': days_back,
                   'totals': totals,
                   'categories': categories,})
        
def user_login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return HttpResponseRedirect('/alesheets/')
    else:
        return HttpResponse('User not found or password incorrect. <a href="/alesheets/login/">try again</a>')

def user_logout(request):
    logout(request)
    return render(request, 'registration/logout.html')
