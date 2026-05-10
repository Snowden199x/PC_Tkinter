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

def change_password(org_id: int, new_password: str) -> None:
    from werkzeug.security import generate_password_hash
    hashed = generate_password_hash(new_password)
    _sb.table("organizations").update({
        "password": hashed,
        "must_change_password": False,
    }).eq("id", org_id).execute()

def get_home_data(org_id: int) -> dict:

    # wallets
    wallets_res = _sb.table("wallets").select("id,name").eq("organization_id", org_id).eq("status", "active").execute()
    wallets = wallets_res.data or []
    wallet_ids = [w["id"] for w in wallets]
    wallet_name_map = {w["id"]: w["name"] for w in wallets}

    # transactions for all wallets
    transactions = []
    if wallet_ids:
        tx_res = _sb.table("wallet_transactions").select("*").in_("wallet_id", wallet_ids).order("date_issued", desc=True).limit(20).execute()
        transactions = tx_res.data or []

    # this month income & expense
    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    month_tx = [t for t in transactions if (t["date_issued"] or "").startswith(month_str)]
    income_month  = sum(t["price"] * t["quantity"] for t in month_tx if t["kind"] == "income")
    expense_month = sum(t["price"] * t["quantity"] for t in month_tx if t["kind"] == "expense")

    # total balance across all wallets
    total_balance = sum(
        (t["price"] * t["quantity"]) if t["kind"] == "income"
        else -(t["price"] * t["quantity"])
        for t in transactions
    )

    # ── Wallets overview — per budget-folder, same as web /api/wallets/overview ──
    wallets_overview = []
    if wallet_ids:
        bud_res = _sb.table("wallet_budgets") \
            .select("id,wallet_id,amount,year,month_id,months(month_name)") \
            .in_("wallet_id", wallet_ids).execute()
        budgets = bud_res.data or []
        budget_ids = [b["id"] for b in budgets]

        if budget_ids:
            folder_tx_res = _sb.table("wallet_transactions") \
                .select("budget_id,kind,quantity,price,date_issued") \
                .in_("budget_id", budget_ids).execute()
            folder_txs = folder_tx_res.data or []
        else:
            folder_txs = []

        by_folder = {}
        for b in budgets:
            fid = b["id"]
            month_name = ""
            if b.get("months"):
                month_name = (b["months"].get("month_name") or "").upper()
            wallet_n = wallet_name_map.get(b["wallet_id"], "")
            by_folder[fid] = {
                "id":             fid,
                "wallet_id":      b["wallet_id"],
                "name":           f"{month_name} – {wallet_n}" if wallet_n else month_name,
                "budget":         float(b.get("amount") or 0),
                "total_income":   0.0,
                "total_expenses": 0.0,
                "last_activity":  None,
            }

        for tx in folder_txs:
            fid = tx.get("budget_id")
            if fid not in by_folder:
                continue
            amt = float(tx.get("price", 0)) * int(tx.get("quantity", 1))
            if tx.get("kind") == "income":
                by_folder[fid]["total_income"] += amt
            elif tx.get("kind") == "expense":
                by_folder[fid]["total_expenses"] += amt
            ts = tx.get("date_issued")
            if ts:
                cur = by_folder[fid]["last_activity"]
                if not cur or ts > cur:
                    by_folder[fid]["last_activity"] = ts

        # only folders with activity, sorted by most recent
        active = [v for v in by_folder.values()
                  if v["total_income"] > 0 or v["total_expenses"] > 0]
        active.sort(key=lambda x: x["last_activity"] or "", reverse=True)
        wallets_overview = active

    # reports submitted
    try:
        rep_res = _sb.table("financial_reports") \
            .select("id", count="exact") \
            .eq("organization_id", org_id) \
            .in_("status", ["Submitted", "Approved"]) \
            .not_.is_("wallet_id", None) \
            .execute()
        reports_submitted = rep_res.count or 0
    except Exception:
        reports_submitted = 0

    return {
        "total_balance":     total_balance,
        "income_month":      income_month,
        "expense_month":     expense_month,
        "reports":           reports_submitted,
        "wallets_overview":  wallets_overview,   # new — per-folder with budget/income/expense
        "wallets":           [(w["name"], 0) for w in wallets],  # kept for compat
        "transactions":      transactions[:10],
        "wallet_map":        wallet_name_map,
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
                            year: int = None, month: int = None,
                            budget_id: int = None) -> list:
    q = _sb.table("wallet_transactions").select("*").eq("wallet_id", wallet_id)
    if budget_id is not None:
        q = q.eq("budget_id", budget_id)
    if kind_filter != "all":
        q = q.eq("kind", kind_filter)
    return q.order("date_issued", desc=True).execute().data or []


def get_wallet_receipts(wallet_id: int, budget_id: int = None) -> list:
    """Return receipts for a wallet, optionally scoped to a specific month (budget_id)."""
    q = _sb.table("wallet_receipts").select("*").eq("wallet_id", wallet_id)
    if budget_id is not None:
        q = q.eq("budget_id", budget_id)
    return q.order("receipt_date", desc=True).execute().data or []


def add_wallet_receipt(wallet_id: int, budget_id: int,
                       org_id: int, org_name: str,
                       wallet_name: str, month_name: str,
                       file_bytes: bytes, filename: str,
                       description: str, receipt_date: str) -> dict:
    """Upload receipt file to Supabase Storage and insert wallet_receipts row."""
    import re
    from uuid import uuid4

    def _slug(s):
        return re.sub(r"[^a-z0-9]+", "-", (s or "unknown").lower()).strip("-")

    ext = os.path.splitext(filename)[1] or ".png"
    path = f"{_slug(org_name)}/{_slug(wallet_name)}/{_slug(month_name)}/{uuid4()}{ext}"

    _sb.storage.from_("Receipts").upload(path, file_bytes)

    res = _sb.table("wallet_receipts").insert({
        "wallet_id":    wallet_id,
        "budget_id":    budget_id,
        "file_url":     path,
        "description":  description,
        "receipt_date": receipt_date,
    }).execute()
    return res.data[0] if res.data else {}


def get_receipt_public_url(file_path: str) -> str:
    """Return the public URL for a receipt stored in Supabase Storage."""
    public = _sb.storage.from_("Receipts").get_public_url(file_path)
    return public.get("publicUrl") if isinstance(public, dict) else (public or "")


def download_receipt_bytes(file_path: str) -> bytes:
    """Download raw bytes of a receipt file from Supabase Storage."""
    return _sb.storage.from_("Receipts").download(file_path)


def get_receipt_download_url(file_path: str) -> str:
    """Return a download-forced public URL for a receipt."""
    try:
        public = _sb.storage.from_("Receipts").get_public_url(
            file_path, {"download": True})
        return public.get("publicUrl") if isinstance(public, dict) else (public or "")
    except Exception:
        # fallback: plain public URL works for download too
        return get_receipt_public_url(file_path)


def delete_receipt(receipt_id: int) -> None:
    """Delete receipt row and its file from Supabase Storage."""
    res = _sb.table("wallet_receipts").select("file_url").eq("id", receipt_id).limit(1).execute()
    if res.data:
        file_path = res.data[0].get("file_url") or ""
        if file_path:
            try:
                _sb.storage.from_("Receipts").remove([file_path])
            except Exception:
                pass
    _sb.table("wallet_receipts").delete().eq("id", receipt_id).execute()


def get_wallet_reports(org_id: int, wallet_id: int) -> list:
    return _sb.table("financial_reports").select("*").eq("organization_id", org_id).eq("wallet_id", wallet_id).order("created_at", desc=True).execute().data or []


def get_wallet_archives(org_id: int, wallet_id: int, budget_id: int) -> list:
    """Return financial_report_archives for this specific wallet month (budget_id)."""
    return (_sb.table("financial_report_archives")
              .select("*")
              .eq("organization_id", org_id)
              .eq("wallet_id", wallet_id)
              .eq("budget_id", budget_id)
              .order("created_at", desc=True)
              .execute().data or [])


def get_wallet_budget(wallet_id: int, year: int, month: int) -> float:
    res = _sb.table("wallet_budgets").select("amount").eq("wallet_id", wallet_id).eq("year", year).eq("month_id", month).execute()
    return res.data[0]["amount"] if res.data else 0.0


def upsert_wallet_budget(budget_id: int, amount: float) -> dict:
    res = _sb.table("wallet_budgets").update({"amount": amount}).eq("id", budget_id).execute()
    return res.data[0] if res.data else {}


def add_wallet_transaction(wallet_id: int, budget_id: int, kind: str,
                           date_issued: str, quantity: int,
                           income_type: str, particulars: str,
                           description: str, price: float) -> dict:
    payload = {
        "wallet_id":   wallet_id,
        "budget_id":   budget_id,
        "kind":        kind,
        "date_issued": date_issued,
        "quantity":    quantity,
        "income_type": income_type or None,
        "particulars": particulars or None,
        "description": description,
        "price":       price,
    }
    res = _sb.table("wallet_transactions").insert(payload).execute()
    return res.data[0] if res.data else {}


def update_wallet_transaction(tx_id: int, date_issued: str, quantity: int,
                              income_type: str, particulars: str,
                              description: str, price: float) -> dict:
    payload = {
        "date_issued": date_issued,
        "quantity":    quantity,
        "income_type": income_type or None,
        "particulars": particulars or None,
        "description": description,
        "price":       price,
    }
    res = _sb.table("wallet_transactions").update(payload).eq("id", tx_id).execute()
    return res.data[0] if res.data else {}


def delete_wallet_transaction(tx_id: int) -> None:
    _sb.table("wallet_transactions").delete().eq("id", tx_id).execute()


def add_financial_report(org_id: int, wallet_id: int, budget_id: int,
                         event_name: str, date_prepared: str, report_no: str,
                         budget: float, total_income: float, total_expense: float,
                         reimbursement: float, prev_fund: float,
                         budget_in_bank: float) -> dict:
    # resolve report_month from wallet_budgets → months.month_name
    # (OSAS view queries financial_reports.report_month to find the record)
    report_month_value = None
    try:
        wb = _sb.table("wallet_budgets") \
            .select("months(month_name)").eq("id", budget_id).single().execute()
        if wb.data and wb.data.get("months"):
            report_month_value = (wb.data["months"].get("month_name") or "").lower()
    except Exception:
        pass

    payload = {
        "organization_id":    org_id,
        "wallet_id":          wallet_id,
        "budget_id":          budget_id,
        "event_name":         event_name,
        "date_prepared":      date_prepared,
        "report_no":          report_no or None,
        "budget":             budget,
        "total_income":       total_income,
        "total_expense":      total_expense,
        "reimbursement":      reimbursement,
        "previous_fund":      prev_fund,
        "budget_in_the_bank": budget_in_bank,
        "status":             "Pending Review",
        "notes":              None,
        "checklist":          {},
        "report_month":       report_month_value,   # ← required by OSAS view
    }

    # upsert: update if a row already exists for this wallet+budget, else insert
    existing = _sb.table("financial_reports").select("id") \
        .eq("organization_id", org_id) \
        .eq("wallet_id", wallet_id) \
        .eq("budget_id", budget_id) \
        .eq("status", "Pending Review") \
        .limit(1).execute()

    if existing.data:
        rep_id = existing.data[0]["id"]
        _sb.table("financial_reports").update(payload).eq("id", rep_id).execute()
        res = _sb.table("financial_reports").select("*").eq("id", rep_id).execute()
    else:
        res = _sb.table("financial_reports").insert(payload).execute()

    return res.data[0] if res.data else {}


def get_latest_report(org_id: int, wallet_id: int, budget_id: int) -> dict:
    """Return the most recent financial report for this specific wallet month (budget_id)."""
    if not budget_id:
        return {}
    res = _sb.table("financial_reports").select("*") \
        .eq("organization_id", org_id) \
        .eq("wallet_id", wallet_id) \
        .eq("budget_id", budget_id) \
        .order("created_at", desc=True).limit(1).execute()
    return res.data[0] if res.data else {}


def get_profile(org_id: int) -> dict:
    org = _sb.table("organizations").select("*").eq("id", org_id).execute().data
    if not org:
        return {}
    org = org[0]
    dept = _sb.table("departments").select("dept_name").eq("id", org.get("department_id", 0)).execute().data
    dept_name = dept[0]["dept_name"] if dept else ""
    profile_row = _sb.table("profile_users").select("*").eq("organization_id", org_id).execute().data
    profile = profile_row[0] if profile_row else {}

    # resolve storage path → public URL (same as web's get_profile)
    photo_url = ""
    raw_path = profile.get("profile_photo_url") or ""
    if raw_path:
        try:
            bucket = "profile-photos"
            public = _sb.storage.from_(bucket).get_public_url(raw_path)
            photo_url = public.get("publicUrl") if isinstance(public, dict) else (public or "")
        except Exception:
            photo_url = raw_path  # fallback: keep raw path

    return {
        "org_name":           org.get("org_name", ""),
        "org_short_name":     profile.get("org_short_name") or "",
        "department":         dept_name,
        "school":             profile.get("school_name") or "Laguna State Polytechnic University, Sta. Cruz, Laguna (LSPU-SCC)",
        "email":              profile.get("email") or "",
        "accreditation_date": org.get("accreditation_date", ""),
        "status":             org.get("status", ""),
        "profile_photo_url":  photo_url,
    }


def get_officers(org_id: int) -> list:
    res = _sb.table("profile_officers").select("*").eq("organization_id", org_id).order("term_start").execute()
    return res.data or []


def update_profile(org_id: int, org_short_name: str = None, email: str = None) -> dict:
    """Update editable profile fields in profile_users. Returns updated row or raises."""
    prof_update = {}
    if org_short_name is not None:
        prof_update["org_short_name"] = org_short_name
    if email is not None:
        prof_update["email"] = email

    if not prof_update:
        return {}

    existing = _sb.table("profile_users").select("id").eq("organization_id", org_id).limit(1).execute()
    if existing.data:
        res = _sb.table("profile_users").update(prof_update).eq("organization_id", org_id).execute()
    else:
        prof_update["organization_id"] = org_id
        prof_update.setdefault("school_name", "Laguna State Polytechnic University, Sta. Cruz, Laguna (LSPU-SCC)")
        res = _sb.table("profile_users").insert(prof_update).execute()

    return res.data[0] if res.data else {}


def update_profile_photo(org_id: int, image_bytes: bytes, ext: str) -> str:
    """Upload photo to Supabase Storage and update profile_users. Returns public URL."""
    from uuid import uuid4
    bucket = "profile-photos"
    path = f"orgs/{org_id}/org-{org_id}-{uuid4()}.{ext}"
    _sb.storage.from_(bucket).upload(path, image_bytes)

    existing = _sb.table("profile_users").select("id").eq("organization_id", org_id).limit(1).execute()
    if existing.data:
        _sb.table("profile_users").update({"profile_photo_url": path}).eq("organization_id", org_id).execute()
    else:
        _sb.table("profile_users").insert({
            "organization_id": org_id,
            "profile_photo_url": path,
        }).execute()

    public = _sb.storage.from_(bucket).get_public_url(path)
    return public.get("publicUrl") if isinstance(public, dict) else public


def create_officer(org_id: int, name: str, position: str,
                   term_start: str, term_end: str, status: str) -> dict:
    payload = {
        "organization_id": org_id,
        "name":       name,
        "position":   position,
        "term_start": term_start or None,
        "term_end":   term_end or None,
        "status":     status or "active",
    }
    res = _sb.table("profile_officers").insert(payload).execute()
    return res.data[0] if res.data else {}


def update_officer(officer_id: int, org_id: int, name: str, position: str,
                   term_start: str, term_end: str, status: str) -> dict:
    payload = {k: v for k, v in {
        "name":       name,
        "position":   position,
        "term_start": term_start or None,
        "term_end":   term_end or None,
        "status":     status,
    }.items() if v is not None}
    res = (_sb.table("profile_officers")
             .update(payload)
             .eq("id", officer_id)
             .eq("organization_id", org_id)
             .execute())
    return res.data[0] if res.data else {}


def delete_officer(officer_id: int, org_id: int) -> None:
    _sb.table("profile_officers").delete().eq("id", officer_id).eq("organization_id", org_id).execute()


def request_password_reset(identifier: str) -> str:
    """
    Mirror of web's POST /pres/forgot-password.
    Generates a reset code, saves it to profile_users, and sends the
    same HTML email as the web using Gmail SMTP (credentials from .env).
    Returns the email address if found, None otherwise.
    """
    import secrets, string, smtplib, os as _os2
    from datetime import datetime as _dt, timezone, timedelta
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # 1. look up by email in profile_users
    res = _sb.table("profile_users").select("id,organization_id,email") \
        .eq("email", identifier).limit(1).execute()

    # 2. fallback: look up by org username
    if not res.data:
        org_res = _sb.table("organizations").select("id,username") \
            .eq("username", identifier).limit(1).execute()
        if org_res.data:
            org_id = org_res.data[0]["id"]
            res = _sb.table("profile_users").select("id,organization_id,email") \
                .eq("organization_id", org_id).limit(1).execute()

    if not res.data:
        return None   # not found — caller shows generic message

    user  = res.data[0]
    email = user.get("email")
    if not email:
        return None

    # 3. get org name for the email greeting
    org_name = "PockiTrack Organization"
    org_id   = user.get("organization_id")
    if org_id:
        org_res2 = _sb.table("organizations").select("org_name") \
            .eq("id", org_id).limit(1).execute()
        if org_res2.data:
            org_name = org_res2.data[0].get("org_name") or org_name

    # 4. generate 6-digit code and save with 15-min expiry
    code       = "".join(secrets.choice(string.digits) for _ in range(6))
    expires_at = (_dt.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    _sb.table("profile_users").update({
        "reset_code":            code,
        "reset_code_expires_at": expires_at,
    }).eq("id", user["id"]).execute()

    # 5. build reset link — points to the web app's change-password page.
    #    WEB_BASE_URL in .env must match the address you use to open the web app
    #    in your browser (e.g. http://192.168.1.13:5000).
    web_base   = os.getenv("WEB_BASE_URL", "http://192.168.1.13:5000").rstrip("/")
    reset_link = f"{web_base}/pres/change-password?code={code}&email={email}"

    banner_url   = os.getenv("BANNER_URL", "")
    requested_at = _dt.now().strftime("%b %d, %Y %I:%M %p")

    # 6. build HTML body from the Python template (no file reading needed)
    from email_templates import reset_password_email
    html_body = reset_password_email(
        org_name     = org_name,
        reset_link   = reset_link,
        to_email     = email,
        requested_at = requested_at,
        banner_url   = banner_url,
    )

    # 7. send via Gmail SMTP
    mail_user = os.getenv("MAIL_USERNAME", "")
    mail_pass = os.getenv("MAIL_PASSWORD", "")

    if mail_user and mail_pass:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "PockiTrack Password Reset"
        msg["From"]    = mail_user
        msg["To"]      = email

        plain = (
            f"Hi {org_name},\n\n"
            "You requested to reset your PockiTrack password.\n\n"
            f"Use this link (valid 15 minutes):\n{reset_link}\n\n"
            "If you did not request this, ignore this email.\n\n"
            "Regards,\nPockiTrack Team"
        )
        msg.attach(MIMEText(plain, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(mail_user, mail_pass)
            smtp.sendmail(mail_user, email, msg.as_string())

    return email


def submit_report(org_id: int, wallet_id: int, budget_id: int) -> dict:
    """
    Mirror of web's POST /reports/<wallet_id>/submit.
    1. Marks the financial_report as Submitted
    2. Creates archive snapshot (summary + transactions + receipts)
    3. Sends OSAS notification
    4. Updates OSAS checklist/status
    Returns the archive row.
    """
    from datetime import datetime as _dt

    # find the pending report for this wallet+budget
    rep_res = _sb.table("financial_reports").select("*") \
        .eq("organization_id", org_id) \
        .eq("wallet_id", wallet_id) \
        .eq("budget_id", budget_id) \
        .eq("status", "Pending Review") \
        .order("created_at", desc=True).limit(1).execute()

    if not rep_res.data:
        raise ValueError("No pending report found for this wallet month.")

    rep    = rep_res.data[0]
    rep_id = rep["id"]

    # 1. mark as Submitted
    _sb.table("financial_reports").update({
        "status":          "Submitted",
        "submission_date": _dt.utcnow().date().isoformat(),
        "updated_at":      _dt.utcnow().isoformat(),
    }).eq("id", rep_id).execute()

    # 2. compute remaining
    budget_val    = float(rep.get("budget") or 0)
    total_expense = float(rep.get("total_expense") or 0)
    reimb         = float(rep.get("reimbursement") or 0)
    prev_fund     = float(rep.get("previous_fund") or 0)
    remaining     = budget_val - total_expense - reimb + prev_fund

    # 3. insert archive summary
    arch_ins = _sb.table("financial_report_archives").insert({
        "organization_id": org_id,
        "wallet_id":       wallet_id,
        "budget_id":       budget_id,
        "report_id":       rep_id,
        "report_no":       rep.get("report_no"),
        "event_name":      rep.get("event_name"),
        "date_prepared":   rep.get("date_prepared"),
        "budget":          budget_val,
        "total_expense":   total_expense,
        "reimbursement":   reimb,
        "previous_fund":   prev_fund,
        "remaining":       remaining,
        "file_url":        None,
    }).execute()
    archive_id = arch_ins.data[0]["id"]

    # 4. archive transactions
    tx_res = _sb.table("wallet_transactions") \
        .select("date_issued,quantity,particulars,description,price,kind") \
        .eq("wallet_id", wallet_id).eq("budget_id", budget_id).execute()
    txs = tx_res.data or []
    if txs:
        _sb.table("financial_report_archive_transactions").insert([{
            "archive_id":  archive_id,
            "date_issued": tx["date_issued"],
            "quantity":    tx["quantity"],
            "particulars": tx.get("particulars"),
            "description": tx["description"],
            "price":       float(tx["price"]),
            "kind":        tx["kind"],
        } for tx in txs]).execute()

    # 5. archive receipts
    rc_res = _sb.table("wallet_receipts") \
        .select("description,receipt_date,file_url") \
        .eq("wallet_id", wallet_id).eq("budget_id", budget_id).execute()
    receipts = rc_res.data or []
    if receipts:
        _sb.table("financial_report_archive_receipts").insert([{
            "archive_id":   archive_id,
            "description":  r["description"],
            "receipt_date": r["receipt_date"],
            "file_url":     r["file_url"],
        } for r in receipts]).execute()

    # 6. OSAS notification (best-effort — never crash submit on failure)
    try:
        org_res = _sb.table("organizations").select("org_name") \
            .eq("id", org_id).limit(1).execute()
        org_name = org_res.data[0]["org_name"] if org_res.data else "Organization"

        # get month name for the notification message
        wb_res = _sb.table("wallet_budgets") \
            .select("months(month_name)").eq("id", budget_id).limit(1).execute()
        month_label = ""
        if wb_res.data and wb_res.data[0].get("months"):
            month_label = (wb_res.data[0]["months"].get("month_name") or "").title()

        message = (f'has a report "Pending Review for {month_label}"'
                   if month_label else 'has a report "Pending Review"')

        _sb.table("osas_notifications").insert({
            "org_id":    org_id,
            "report_id": rep_id,
            "org_name":  org_name,
            "message":   message,
        }).execute()
    except Exception:
        pass

    # 7. update OSAS checklist/status (best-effort)
    try:
        wb_res2 = _sb.table("wallet_budgets") \
            .select("months(month_name)").eq("id", budget_id).single().execute()
        if wb_res2.data and wb_res2.data.get("months"):
            month_key = (wb_res2.data["months"].get("month_name") or "").lower()
            fr_res = _sb.table("financial_reports").select("*") \
                .eq("organization_id", org_id) \
                .is_("wallet_id", None).is_("budget_id", None) \
                .limit(1).execute()
            if fr_res.data:
                master = fr_res.data[0]
                checklist = master.get("checklist") or {}
                month_keys = ["august","september","october","november","december",
                              "january","february","march","april","may"]
                if month_key in month_keys:
                    checklist[month_key] = True
                received = sum(1 for k in month_keys if checklist.get(k))
                total    = len(month_keys)
                new_status = ("Completed" if received == total
                              else "In Review" if received > 0
                              else "Pending Review")
                _sb.table("financial_reports").update({
                    "checklist":  checklist,
                    "status":     new_status,
                    "updated_at": _dt.utcnow().isoformat(),
                }).eq("id", master["id"]).execute()
    except Exception:
        pass

    return arch_ins.data[0]
