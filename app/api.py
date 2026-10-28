import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app import db
from app.expenses import CATEGORIES
from app.models import Budget, Expense, User

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    return jsonify(status="ok")


def current_api_user():
    try:
        return db.session.get(User, int(get_jwt_identity()))
    except (TypeError, ValueError):
        return None


def user_json(user):
    return {"id": user.id, "name": user.name, "email": user.email}


def transaction_json(item):
    return {
        "id": item.id,
        "title": item.title,
        "amount": float(item.amount),
        "kind": item.kind,
        "category": item.category,
        "spent_on": item.spent_on.isoformat(),
        "note": item.note or "",
    }


def parse_transaction(data):
    title = str(data.get("title", "")).strip()
    category = data.get("category")
    kind = data.get("kind", "expense")
    note = str(data.get("note", "")).strip()
    try:
        amount = Decimal(str(data.get("amount", "")))
        spent_on = date.fromisoformat(str(data.get("spent_on", "")))
    except (InvalidOperation, ValueError):
        return None, "Enter a valid amount and date."
    if not title or len(title) > 120:
        return None, "Description is required and must be 120 characters or fewer."
    if not amount.is_finite() or amount <= 0 or amount > Decimal("9999999999.99"):
        return None, "Amount must be greater than zero."
    if kind not in ("expense", "income"):
        return None, "Choose expense or income."
    if category not in CATEGORIES:
        return None, "Choose a valid category."
    if len(note) > 280:
        return None, "Notes must be 280 characters or fewer."
    return {"title": title, "amount": amount, "kind": kind, "category": category, "spent_on": spent_on, "note": note}, None


def parse_month(raw):
    try:
        start = datetime.strptime(raw, "%Y-%m").date().replace(day=1)
    except (TypeError, ValueError):
        start = date.today().replace(day=1)
    end = date(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1)
    return start.strftime("%Y-%m"), start, end


@bp.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    password = str(data.get("password", ""))
    try:
        email = validate_email(str(data.get("email", "")), check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        return jsonify(message="Enter a valid email address."), 400
    if len(name) < 2 or len(name) > 80:
        return jsonify(message="Name must be between 2 and 80 characters."), 400
    if len(password) < 8 or len(password) > 128:
        return jsonify(message="Password must be at least 8 characters."), 400
    if User.query.filter_by(email=email).first():
        return jsonify(message="An account with this email already exists."), 409
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(access_token=create_access_token(identity=str(user.id)), user=user_json(user)), 201


@bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(message="That email and password combination was not found."), 401
    return jsonify(access_token=create_access_token(identity=str(user.id)), user=user_json(user))


@bp.get("/auth/me")
@jwt_required()
def me():
    user = current_api_user()
    if not user:
        return jsonify(message="Account not found."), 404
    return jsonify(user=user_json(user))


@bp.get("/dashboard")
@jwt_required()
def dashboard():
    user = current_api_user()
    if not user:
        return jsonify(message="Account not found."), 404
    month, start, end = parse_month(request.args.get("month"))
    query = Expense.query.filter_by(user_id=user.id)
    date_from = date_to = None
    try:
        if request.args.get("from"):
            date_from = date.fromisoformat(request.args["from"])
    except ValueError:
        pass
    try:
        if request.args.get("to"):
            date_to = date.fromisoformat(request.args["to"])
    except ValueError:
        pass
    if date_from is None and date_to is None:
        query = query.filter(Expense.spent_on >= start, Expense.spent_on < end)
    if date_from:
        query = query.filter(Expense.spent_on >= date_from)
    if date_to:
        query = query.filter(Expense.spent_on <= date_to)
    category = request.args.get("category")
    kind = request.args.get("kind")
    if category in CATEGORIES:
        query = query.filter_by(category=category)
    if kind in ("expense", "income"):
        query = query.filter_by(kind=kind)
    sort = request.args.get("sort", "newest")
    order = Expense.amount.asc() if sort == "amount_asc" else Expense.amount.desc() if sort == "amount_desc" else Expense.spent_on.asc() if sort == "oldest" else Expense.spent_on.desc()
    entries = query.order_by(order, Expense.id.desc()).limit(150).all()
    month_entries = Expense.query.filter(Expense.user_id == user.id, Expense.spent_on >= start, Expense.spent_on < end).all()
    income = sum((item.amount for item in month_entries if item.kind == "income"), Decimal("0"))
    spent = sum((item.amount for item in month_entries if item.kind == "expense"), Decimal("0"))
    category_totals = {}
    for item in month_entries:
        if item.kind == "expense":
            category_totals[item.category] = category_totals.get(item.category, Decimal("0")) + item.amount
    budget = Budget.query.filter_by(user_id=user.id, month=month).first()
    trend = []
    for offset in range(5, -1, -1):
        index = start.year * 12 + start.month - 1 - offset
        year, month_index = divmod(index, 12)
        trend_start = date(year, month_index + 1, 1)
        trend_end = date(year + (month_index == 11), 1 if month_index == 11 else month_index + 2, 1)
        rows = Expense.query.filter(Expense.user_id == user.id, Expense.kind == "expense", Expense.spent_on >= trend_start, Expense.spent_on < trend_end).all()
        trend.append({"month": trend_start.strftime("%b"), "total": float(sum((item.amount for item in rows), Decimal("0")))})
    return jsonify(
        month=month,
        income=float(income),
        spent=float(spent),
        balance=float(income - spent),
        budget=float(budget.amount) if budget else None,
        category_totals={key: float(value) for key, value in category_totals.items()},
        trend=trend,
        transactions=[transaction_json(item) for item in entries],
        categories=CATEGORIES,
    )


@bp.post("/transactions")
@jwt_required()
def create_transaction():
    user = current_api_user()
    if not user:
        return jsonify(message="Account not found."), 401
    values, error = parse_transaction(request.get_json(silent=True) or {})
    if error:
        return jsonify(message=error), 400
    item = Expense(user_id=user.id, **values)
    db.session.add(item)
    db.session.commit()
    return jsonify(transaction=transaction_json(item)), 201


@bp.patch("/transactions/<int:transaction_id>")
@jwt_required()
def update_transaction(transaction_id):
    user = current_api_user()
    if not user:
        return jsonify(message="Account not found."), 401
    item = Expense.query.filter_by(id=transaction_id, user_id=user.id).first()
    if not item:
        return jsonify(message="Transaction not found."), 404
    values, error = parse_transaction(request.get_json(silent=True) or {})
    if error:
        return jsonify(message=error), 400
    for key, value in values.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify(transaction=transaction_json(item))


@bp.delete("/transactions/<int:transaction_id>")
@jwt_required()
def delete_transaction(transaction_id):
    user = current_api_user()
    if not user:
        return jsonify(message="Account not found."), 401
    item = Expense.query.filter_by(id=transaction_id, user_id=user.id).first()
    if not item:
        return jsonify(message="Transaction not found."), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify(message="Transaction deleted.")


@bp.put("/budget")
@jwt_required()
def save_budget():
    user = current_api_user()
    if not user:
        return jsonify(message="Account not found."), 401
    data = request.get_json(silent=True) or {}
    month, _, _ = parse_month(data.get("month"))
    try:
        amount = Decimal(str(data.get("amount", "")))
        if not amount.is_finite() or amount <= 0 or amount > Decimal("9999999999.99"):
            raise InvalidOperation
    except InvalidOperation:
        return jsonify(message="Enter a valid budget amount above zero."), 400
    budget = Budget.query.filter_by(user_id=user.id, month=month).first()
    if budget is None:
        budget = Budget(user_id=user.id, month=month, amount=amount)
        db.session.add(budget)
    else:
        budget.amount = amount
    db.session.commit()
    return jsonify(month=month, amount=float(budget.amount))


@bp.get("/export.csv")
@jwt_required()
def export_csv():
    user = current_api_user()
    if not user:
        return jsonify(message="Account not found."), 401
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Description", "Category", "Amount", "Note"])
    rows = Expense.query.filter_by(user_id=user.id).order_by(Expense.spent_on.desc()).all()
    for item in rows:
        values = [item.title, item.category, item.note or ""]
        safe_values = ["'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value for value in values]
        writer.writerow([item.spent_on.isoformat(), item.kind, safe_values[0], safe_values[1], f"{item.amount:.2f}", safe_values[2]])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=transactions.csv"})
