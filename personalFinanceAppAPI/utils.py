from .models import Account, Item, Transaction
from datetime import datetime

def clean_accounts_data(item_id, accounts):
    accounts_data = []

    for acc in accounts:
        data = {}
        data['item'] = item_id
        data['account_id'] = acc['account_id']

        if not 'balances' in acc:
            acc['balances'] = {}
            acc['balances']['available'] = 0
            acc['balances']['current'] = 0

        if acc['balances']['available'] is None:
            acc['balances']['available'] = 0
        if acc['balances']['current'] is None:
            acc['balances']['current'] = 0

        if not 'name' in acc or acc['name'] is None:
            acc['name'] = ""
        if not 'type' in acc or acc['type'] is None:
            acc['type'] = ""
        if not 'subtype' in acc or acc['subtype'] is None:
            acc['subtype'] = ""

        data['available_balance'] = acc['balances']['available']
        data['current_balance'] = acc['balances']['current']
        data['name'] = acc['name']
        data['account_type'] = str(acc['type'])
        data['account_subtype'] = str(acc['subtype'])

        accounts_data.append(data)
    print(f'CLEANED ACCOUNT DATA: {accounts_data}')
    
    return accounts_data

def clean_transaction_data(transactions):
    transaction_data = []

    for tran in transactions:
        data = {}
        data['account'] = Account.objects.filter(account_id = tran['account_id'])[0].pk
        data['transaction_id'] = tran['transaction_id']

        if not 'amount' in tran or tran['amount'] is None:
            tran['amount'] = 0
        
        if not 'date' in tran or tran['date'] is None:
            tran['date'] = datetime.now()
        
        if not 'name' in tran or tran['name'] is None:
            tran['name'] = ''

        if not 'payment_channel' in tran or tran['payment_channel'] is None:
            tran['payment_channel'] = ''

        if not 'category' in tran or tran['category'] is None:
            tran['category'] = []

        data['amount'] = tran['amount']
        data['date'] = tran['date']
        data['name'] = tran['name']
        data['payment_channel'] = tran['payment_channel']
        data['primary_category'] = tran['category'][0]
        if len(tran['category']) > 1:
            data['detailed_category'] = tran['category'][1]
        else:
            data['detailed_category'] = ''


        transaction_data.append(data)
    print(f'CLEANED TRANSACTION DATA: {transaction_data}')

    return transaction_data

def remove_duplicate_accounts(accounts):
    for account in accounts:
        try:
            dbAccount = Account.objects.get(account_id=account['account_id'])
        except:
            dbAccount = None
        if not dbAccount is None:
            Account.objects.get(account_id=account['account_id']).delete()


def remove_duplicate_transactions(transactions):
    for tran in transactions:
        try:
            dbTransaction = Transaction.objects.filter(transaction_id = tran['transaction_id']).delete()
        except:
            dbTransaction = 'No Item For User Found'
    return dbTransaction
    

def remove_duplicate_user_items(user):
    try:
        item = Item.objects.filter(user = user).delete()
    except:
        item = 'No Item For User Found'
    
    return item

