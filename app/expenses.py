import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app import db
from app.models import Budget, Expense

bp = Blueprint("expenses", __name__)
CATEGORIES = ["Food & drink", "Transport", "Home", "Bills", "Shopping", "Health", "Entertainment", "Education", "Travel", "Salary", "Freelance", "Other"]


class ExpenseForm(FlaskForm):
    title = StringField("What was it for?", validators=[DataRequired(), Length(max=120)])
    amount = DecimalField("Amount", places=2, validators=[DataRequired(), NumberRange(min=Decimal("0.01"), max=Decimal("9999999999.99"))])
    kind = SelectField("Type", choices=[("expense", "Expense"), ("income", "Income")], validators=[DataRequired()])
    category = SelectField("Category", choices=[(x, x) for x in CATEGORIES], validators=[DataRequired()])
    spent_on = DateField("Date", validators=[DataRequired()])
    note = TextAreaField("Note", validators=[Optional(), Length(max=280)])
    submit = SubmitField("Save transaction")


def owned_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    if expense is None:
        abort(404)
    return expense


@bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("expenses.dashboard"))
    return redirect(url_for("auth.login"))


@bp.get("/dashboard")
@login_required
def dashboard():
    today = date.today()
    month = request.args.get("month", today.strftime("%Y-%m"))
    try:
        start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
        end = date(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1)
    except ValueError:
        month = today.strftime("%Y-%m")
        start = today.replace(day=1)
        end = date(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1)

    query = Expense.query.filter_by(user_id=current_user.id)
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
    # A date range can span months; otherwise the selected summary month filters the list.
    if date_from is None and date_to is None:
        query = query.filter(Expense.spent_on >= start, Expense.spent_on < end)
    if date_from:
        query = query.filter(Expense.spent_on >= date_from)
    if date_to:
        query = query.filter(Expense.spent_on <= date_to)
    if request.args.get("category") in CATEGORIES:
        query = query.filter_by(category=request.args["category"])
    if request.args.get("kind") in ("expense", "income"):
        query = query.filter_by(kind=request.args["kind"])
    sort = request.args.get("sort", "newest")
    query = query.order_by(Expense.amount.asc() if sort == "amount_asc" else Expense.amount.desc() if sort == "amount_desc" else Expense.spent_on.asc() if sort == "oldest" else Expense.spent_on.desc(), Expense.id.desc())
    entries = query.limit(150).all()
    all_month = Expense.query.filter(Expense.user_id == current_user.id, Expense.spent_on >= start, Expense.spent_on < end).all()
    income = sum((e.amount for e in all_month if e.kind == "income"), Decimal("0"))
    spent = sum((e.amount for e in all_month if e.kind == "expense"), Decimal("0"))
    category_totals = {}
    for item in all_month:
        if item.kind == "expense":
            category_totals[item.category] = category_totals.get(item.category, Decimal("0")) + item.amount
    budget = Budget.query.filter_by(user_id=current_user.id, month=month).first()
    trend_labels, trend_values = [], []
    for offset in range(5, -1, -1):
        idx = start.year * 12 + start.month - 1 - offset
        year, mon = divmod(idx, 12)
        mon += 1
        month_start = date(year, mon, 1)
        month_end = date(year + (mon == 12), 1 if mon == 12 else mon + 1, 1)
        rows = Expense.query.filter(Expense.user_id == current_user.id, Expense.kind == "expense", Expense.spent_on >= month_start, Expense.spent_on < month_end).all()
        trend_labels.append(month_start.strftime("%b"))
        trend_values.append(float(sum((e.amount for e in rows), Decimal("0"))))
    return render_template("dashboard.html", entries=entries, month=month, income=income, spent=spent,
                           balance=income-spent, budget=budget, category_totals=category_totals,
                           trend_labels=trend_labels, trend_values=trend_values, categories=CATEGORIES,
                           filters=request.args)


@bp.route("/transactions/new", methods=["GET", "POST"])
@bp.route("/transactions/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def transaction_form(expense_id=None):
    item = owned_expense(expense_id) if expense_id else None
    form = ExpenseForm(obj=item)
    if not item and request.method == "GET":
        form.spent_on.data = date.today()
        form.kind.data = "expense"
    if form.validate_on_submit():
        if item is None:
            item = Expense(user_id=current_user.id)
            db.session.add(item)
        item.title = form.title.data.strip()
        item.amount = form.amount.data
        item.kind = form.kind.data
        item.category = form.category.data
        item.spent_on = form.spent_on.data
        item.note = (form.note.data or "").strip()
        db.session.commit()
        flash("Transaction saved.", "success")
        return redirect(url_for("expenses.dashboard"))
    return render_template("transaction_form.html", form=form, item=item)


@bp.post("/transactions/<int:expense_id>/delete")
@login_required
def delete_transaction(expense_id):
    item = owned_expense(expense_id)
    db.session.delete(item)
    db.session.commit()
    flash("Transaction deleted.", "success")
    return redirect(url_for("expenses.dashboard"))


@bp.post("/budget")
@login_required
def save_budget():
    month = request.form.get("month", "")
    try:
        datetime.strptime(month, "%Y-%m")
        amount = Decimal(request.form.get("amount", ""))
        if not amount.is_finite() or amount <= 0 or amount > Decimal("9999999999.99"):
            raise InvalidOperation
    except (ValueError, InvalidOperation):
        flash("Enter a valid month and budget above zero.", "error")
        return redirect(url_for("expenses.dashboard"))
    budget = Budget.query.filter_by(user_id=current_user.id, month=month).first()
    if budget is None:
        budget = Budget(user_id=current_user.id, month=month, amount=amount)
        db.session.add(budget)
    else:
        budget.amount = amount
    db.session.commit()
    flash("Monthly budget updated.", "success")
    return redirect(url_for("expenses.dashboard", month=month))


@bp.get("/export.csv")
@login_required
def export_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Description", "Category", "Amount", "Note"])
    rows = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.spent_on.desc()).all()
    for row in rows:
        # Neutralize spreadsheet formulas while retaining readable CSV values.
        cells = [row.title, row.category, row.note or ""]
        safe_cells = ["'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value for value in cells]
        writer.writerow([row.spent_on.isoformat(), row.kind, safe_cells[0], safe_cells[1], f"{row.amount:.2f}", safe_cells[2]])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=transactions.csv"})
