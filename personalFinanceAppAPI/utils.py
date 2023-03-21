from .models import Account, Investment, Item, Transaction
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
        data['account'] = Account.objects.get(account_id = tran['account_id']).pk
        data['transaction_id'] = tran['transaction_id']

        if not 'amount' in tran or tran['amount'] is None:
            tran['amount'] = 0
        
        if not 'date' in tran or tran['date'] is None:
            tran['date'] = datetime.now().date()
        
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

def clean_investment_data(holdings, securities):
    investment_data = []

    for h in holdings:
        new_investment_data = {}
        new_investment_data['account'] = Account.objects.get(account_id = h['account_id']).pk
        
        if not 'security_id' in h or h['security_id'] is None:
            h['security_id'] = ''
        
        if not 'institution_price' in h or h['institution_price'] is None:
            h['institution_price'] = 0
        
        if not 'institution_price_as_of' in h or h['institution_price_as_of'] is None:
            h['institution_price_as_of'] = datetime.now().date()

        if not 'cost_basis' in h or h['cost_basis'] is None:
            h['cost_basis'] = 0

        if not 'quantity' in h or h['quantity'] is None:
            h['quantity'] = 0
        
        new_investment_data['security_id'] = h['security_id']
        
        # Find security name and ticker in list of securities and set the values in our new investment data dict
        for s in securities:
            print(s)
            if s['security_id'] == new_investment_data['security_id']:
                new_investment_data['security_name'] = s['name']
                new_investment_data['security_ticker'] = s['ticker_symbol']
               
        if new_investment_data['security_name'] is None:
            new_investment_data['security_name'] = ''

        if new_investment_data['security_ticker'] is None:
            new_investment_data['security_ticker'] = ''

        new_investment_data['price'] = h['institution_price']
        new_investment_data['price_as_of'] = h['institution_price_as_of']
        new_investment_data['cost_basis'] = h['cost_basis']
        new_investment_data['quantity'] = h['quantity']

        investment_data.append(new_investment_data)
    
    return investment_data


