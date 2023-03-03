from .models import Account, InvestmentHolding, InvestmentSecurity, Item, Transaction
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

def clean_investment_data(holdings, securities):
    investment_holdings_data = []
    investment_securities_data = []

    for h in holdings:
        holdings_data = {}
        holdings_data['account'] = Account.objects.filter(account_id = h['account_id'])[0].pk
        
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
        
        holdings_data['security_id'] = h['security_id']
        print(holdings_data['security_id'])
        holdings_data['price'] = h['institution_price']
        holdings_data['price_as_of'] = h['institution_price_as_of']
        holdings_data['cost_basis'] = h['cost_basis']
        holdings_data['quantity'] = h['quantity']

        investment_holdings_data.append(holdings_data)
    
    for s in securities:
        securities_data = {}

        if not 'security_id' in s or s['security_id'] is None:
            s['security_id'] = ''
        
        if not 'name' in s or s['name'] is None:
            s['name'] = ''

        if not 'ticker_symbol' in s or s['ticker_symbol'] is None:
            s['ticker_symbol'] = ''

        securities_data['security_id'] = s['security_id']
        securities_data['name'] = s['name']
        securities_data['ticker'] = s['ticker_symbol']

        investment_securities_data.append(securities_data)
    
    return investment_holdings_data, investment_securities_data


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
            dbTransaction = 'No Transaction Found'
    return dbTransaction


def remove_duplicate_securities(securities):
    for sec in securities:
        try:
            dbSecurity = InvestmentSecurity.objects.filter(security_id = sec['security_id']).delete()
        except:
            dbSecurity = 'No Transaction Found'
    return dbSecurity

def remove_duplicate_holdings(holdings):
    for hol in holdings:
        try:
            dbHolding = InvestmentHolding.objects.filter(security_id = hol['security_id']).delete()
        except:
            dbHolding = 'No Transaction Found'
    return dbHolding

    
def remove_duplicate_user_items(user):
    try:
        item = Item.objects.filter(user = user).delete()
    except:
        item = 'No Item For User Found'
    
    return item

