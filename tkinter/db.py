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


def get_history_data(org_id: int, year: int, month: int) -> list:
    """Return wallet_transactions for org filtered by year+month, newest first."""
    wallets_res = _sb.table("wallets").select("id,name") \
        .eq("organization_id", org_id).eq("status", "active").execute()
    wallet_ids = [w["id"] for w in (wallets_res.data or [])]
    wallet_map = {w["id"]: w["name"] for w in (wallets_res.data or [])}

    if not wallet_ids:
        return []

    month_str = f"{year}-{month:02d}"
    res = _sb.table("wallet_transactions").select("*") \
        .in_("wallet_id", wallet_ids) \
        .gte("date_issued", f"{month_str}-01") \
        .lt("date_issued",  f"{year}-{month % 12 + 1:02d}-01" if month < 12 else f"{year + 1}-01-01") \
        .order("date_issued", desc=True).execute()

    rows = res.data or []
    for r in rows:
        r["wallet_name"] = wallet_map.get(r["wallet_id"], "—")
    return rows


# Academic year months in order: Aug(8)→Dec(12), Jan(1)→May(5)
_ACAD_MONTHS = [8, 9, 10, 11, 12, 1, 2, 3, 4, 5]
_MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]


def _academic_year(year: int, month: int) -> str:
    """Return academic year string e.g. '2024-2025' for a given year+month."""
    if month >= 8:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


def get_wallets(org_id: int) -> list:
    """Return one entry per academic month (Aug-May) per wallet, with balance."""
    res = _sb.table("wallets").select("id,name").eq("organization_id", org_id).eq("status", "active").execute()
    wallets = res.data or []
    if not wallets:
        return []

    wallet_ids = [w["id"] for w in wallets]

    # all transactions for balance calc
    tx_res = _sb.table("wallet_transactions").select("wallet_id,kind,price,quantity,date_issued").in_("wallet_id", wallet_ids).execute()
    txs = tx_res.data or []

    # all budget rows (year + month_id)
    bud_res = _sb.table("wallet_budgets").select("id,wallet_id,year,month_id,amount").in_("wallet_id", wallet_ids).execute()
    budgets = bud_res.data or []

    entries = []
    for w in wallets:
        wid = w["id"]
        # group budgets by (year, month_id) for this wallet
        bud_map = {(b["year"], b["month_id"]): b for b in budgets if b["wallet_id"] == wid}

        for year, month_id in sorted(bud_map.keys()):
            if month_id not in _ACAD_MONTHS:
                continue
            bud = bud_map[(year, month_id)]
            acad_year = _academic_year(year, month_id)

            # balance = transactions in this month
            month_str = f"{year}-{month_id:02d}"
            next_year  = year + 1 if month_id == 12 else year
            next_month = 1 if month_id == 12 else month_id + 1
            next_str   = f"{next_year}-{next_month:02d}"
            month_txs  = [t for t in txs if t["wallet_id"] == wid
                          and (t["date_issued"] or "") >= f"{month_str}-01"
                          and (t["date_issued"] or "") < f"{next_str}-01"]
            balance = sum(
                (t["price"] * t["quantity"]) if t["kind"] == "income"
                else -(t["price"] * t["quantity"])
                for t in month_txs
            )

            entries.append({
                "id":         wid,
                "budget_id":  bud["id"],
                "name":       f"{_MONTH_NAMES[month_id]} {year} – {w['name']}",
                "wallet_name": w["name"],
                "month":      month_str,
                "month_id":   month_id,
                "month_name": _MONTH_NAMES[month_id].upper(),
                "year":       year,
                "acad_year":  acad_year,
                "balance":    balance,
                "budget":     bud["amount"],
            })

    # sort by academic year then academic month order
    def _sort_key(e):
        idx = _ACAD_MONTHS.index(e["month_id"]) if e["month_id"] in _ACAD_MONTHS else 99
        return (e["acad_year"], idx)

    entries.sort(key=_sort_key)
    return entries


def get_wallet_transactions(wallet_id: int, kind_filter: str = "all",
                            year: int = None, month: int = None) -> list:
    q = _sb.table("wallet_transactions").select("*").eq("wallet_id", wallet_id)
    if year and month:
        month_str = f"{year}-{month:02d}"
        next_year  = year + 1 if month == 12 else year
        next_month = 1 if month == 12 else month + 1
        next_str   = f"{next_year}-{next_month:02d}"
        q = q.gte("date_issued", f"{month_str}-01").lt("date_issued", f"{next_str}-01")
    if kind_filter != "all":
        q = q.eq("kind", kind_filter)
    return q.order("date_issued", desc=True).execute().data or []


def get_wallet_receipts(wallet_id: int) -> list:
    return _sb.table("wallet_receipts").select("*").eq("wallet_id", wallet_id).order("created_at", desc=True).execute().data or []


def get_wallet_reports(org_id: int, wallet_id: int) -> list:
    return _sb.table("financial_reports").select("*").eq("organization_id", org_id).eq("wallet_id", wallet_id).order("created_at", desc=True).execute().data or []


def get_wallet_budget(wallet_id: int, year: int, month: int) -> float:
    res = _sb.table("wallet_budgets").select("amount").eq("wallet_id", wallet_id).eq("year", year).eq("month_id", month).execute()
    return res.data[0]["amount"] if res.data else 0.0
