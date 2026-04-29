import os
from dotenv import load_dotenv
from supabase import create_client
from werkzeug.security import check_password_hash
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def login_organization(username: str, password: str):
    res = _sb.table("organizations").select("*").eq("username", username).execute()
    if not res.data:
        raise ValueError("Organization not found.")
    org = res.data[0]
    if not check_password_hash(org["password"], password):
        raise ValueError("Incorrect password.")
    return org


def get_home_data(org_id: int) -> dict:
    """Fetch all data needed for the home screen for a given org."""

    # wallets
    wallets_res = _sb.table("wallets").select("id,name").eq("organization_id", org_id).eq("status", "active").execute()
    wallets = wallets_res.data or []
    wallet_ids = [w["id"] for w in wallets]

    # transactions for all wallets
    transactions = []
    if wallet_ids:
        tx_res = _sb.table("wallet_transactions").select("*").in_("wallet_id", wallet_ids).order("date_issued", desc=True).limit(20).execute()
        transactions = tx_res.data or []

    # wallet balances: sum income - sum expense per wallet
    wallet_balances = {}
    for w in wallets:
        wid = w["id"]
        wtx = [t for t in transactions if t["wallet_id"] == wid]
        balance = sum(
            (t["price"] * t["quantity"]) if t["kind"] == "income"
            else -(t["price"] * t["quantity"])
            for t in wtx
        )
        wallet_balances[wid] = balance

    total_balance = sum(wallet_balances.values())

    # this month income & expense
    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    month_tx = [t for t in transactions if (t["date_issued"] or "").startswith(month_str)]
    income_month  = sum(t["price"] * t["quantity"] for t in month_tx if t["kind"] == "income")
    expense_month = sum(t["price"] * t["quantity"] for t in month_tx if t["kind"] == "expense")

    # total number of wallets as proxy for events
    total_wallets = len(wallets)

    return {
        "total_balance":  total_balance,
        "total_wallets":  total_wallets,
        "income_month":   income_month,
        "expense_month":  expense_month,
        "wallets":        [(w["name"], wallet_balances[w["id"]]) for w in wallets],
        "transactions":   transactions[:10],
        "wallet_map":     {w["id"]: w["name"] for w in wallets},
    }
