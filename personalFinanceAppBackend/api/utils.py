from datetime import datetime
from logging import getLogger

from django.core.exceptions import MultipleObjectsReturned
from django.db import DatabaseError

from .models import Account

logger = getLogger("personal_finance_app")


def clean_accounts_data(item_id: int, accounts: list) -> list:
    """
    Clean and transform Plaid account data into application format.

    Args:
        item_id: The ID of the Item these accounts belong to
        accounts: List of account data from Plaid API

    Returns:
        List of cleaned account data ready for serialization
    """

    if not isinstance(accounts, list):
        raise ValueError("accounts must be a list")
    if not item_id:
        raise ValueError("item_id is required")

    cleaned_accounts = []

    for account in accounts:
        try:
            if "account_id" not in account:
                logger.error("Account missing account_id field")
                continue

            # Initialize balances with defaults if missing
            balances = account.get("balances", {})

            cleaned_account = {
                "item": item_id,
                "account_id": account["account_id"],
                "available_balance": balances.get("available", 0),
                "current_balance": balances.get("current", 0),
                "name": account.get("name", ""),
                "account_type": str(account.get("type", "")),
                "account_subtype": str(account.get("subtype", "")),
            }

            cleaned_accounts.append(cleaned_account)

        except (KeyError, TypeError) as e:
            logger.error(
                f"Error cleaning account data: {e}",
                extra={
                    "account_id": account.get("account_id", "unknown"),
                    "error": str(e),
                },
            )
            continue

    return cleaned_accounts


def clean_transaction_data(transactions: list) -> list:
    """
    Clean and transform Plaid transaction data into application format.

    Args:
        transactions: List of transaction data from Plaid API

    Returns:
        List of cleaned transaction data ready for serialization
    """
    cleaned_transactions = []

    for transaction in transactions:
        try:
            if "account_id" not in transaction or "transaction_id" not in transaction:
                logger.error("Transaction missing required fields")
                continue

            try:
                account = Account.objects.get(account_id=transaction["account_id"])
            except Account.DoesNotExist:
                logger.error(
                    f"Account not found for transaction {transaction['transaction_id']}"
                )
                continue
            except MultipleObjectsReturned:
                logger.error(
                    f"Multiple accounts found for transaction {transaction['transaction_id']}"
                )
                continue
            except DatabaseError as e:
                logger.error(f"Database error while fetching account: {e}")
                continue

            category = transaction.get("personal_finance_category", {})

            cleaned_transaction = {
                "account": account.pk,
                "transaction_id": transaction["transaction_id"],
                "amount": transaction.get("amount", 0),
                "date": transaction.get("date", datetime.now().date()),
                "name": transaction.get("name", ""),
                "payment_channel": transaction.get("payment_channel", ""),
                "primary_category": category.get("primary", ""),
                "detailed_category": category.get("detailed", ""),
            }

            cleaned_transactions.append(cleaned_transaction)

        except (ValueError, TypeError) as e:
            logger.error(
                f"Error cleaning transaction data: {e}",
                extra={
                    "transaction_id": transaction.get("transaction_id", "unknown"),
                    "error": str(e),
                },
            )
            continue

    return cleaned_transactions


def clean_investment_data(holdings: list, securities: list) -> list:
    """
    Clean and transform Plaid investment data into application format.

    Args:
        holdings: List of holding data from Plaid API
        securities: List of security data from Plaid API

    Returns:
        List of cleaned investment data ready for serialization
    """
    cleaned_investments = []

    # Create a lookup dictionary for securities
    security_lookup = {
        security["security_id"]: {
            "name": security.get("name", ""),
            "ticker": security.get("ticker_symbol", ""),
        }
        for security in securities
        if "security_id" in security
    }

    for holding in holdings:
        try:
            if "account_id" not in holding:
                logger.error("Holding missing account_id field")
                continue

            try:
                account = Account.objects.get(account_id=holding["account_id"])
            except Account.DoesNotExist:
                logger.error(
                    f"Account not found for holding {holding.get('security_id', 'unknown')}"
                )
                continue
            except MultipleObjectsReturned:
                logger.error(
                    f"Multiple accounts found for holding {holding.get('security_id', 'unknown')}"
                )
                continue
            except DatabaseError as e:
                logger.error(f"Database error while fetching account: {e}")
                continue

            security_id = holding.get("security_id", "")
            security_info = security_lookup.get(security_id, {"name": "", "ticker": ""})

            cleaned_investment = {
                "account": account.pk,
                "security_id": security_id,
                "security_name": security_info["name"],
                "security_ticker": security_info["ticker"],
                "price": holding.get("institution_price", 0),
                "price_as_of": holding.get(
                    "institution_price_as_of", datetime.now().date()
                ),
                "cost_basis": holding.get("cost_basis", 0),
                "quantity": holding.get("quantity", 0),
            }

            cleaned_investments.append(cleaned_investment)

        except (ValueError, TypeError) as e:
            logger.error(
                f"Error cleaning investment data: {e}",
                extra={
                    "security_id": holding.get("security_id", "unknown"),
                    "error": str(e),
                },
            )
            continue

    return cleaned_investments


def clean_institution_data(institution_id: str, institution_name: object):
    """
    Clean and transform Plaid institution data into application format.

    Args:
        institution_id: The institution id from Plaid API
        institution: The institution data from Plaid API

    Returns:
        Cleaned institution data ready for serialization
    """
    try:
        cleaned_institution = {
            "institution_id": institution_id,
            "institution_name": institution_name.get("name", ""),
        }

        return cleaned_institution

    except (KeyError, TypeError) as e:
        logger.error(f"Error cleaning institution data: {e}", extra={"error": str(e)})


def clean_item_data(item_id: str, access_token: str, institution_id: str):
    """
    Clean and transform Plaid institution data into application format.

    Args:
        institution_id: The institution id from Plaid API
        institution: The institution data from Plaid API

    Returns:
        Cleaned institution data ready for serialization
    """

    try:
        cleaned_item = {
            "item_id": item_id,
            "institution": institution_id,
            "access_token": access_token,
        }

        return cleaned_item

    except (KeyError, TypeError) as e:
        logger.error(f"Error cleaning item data: {e}", extra={"error": str(e)})
