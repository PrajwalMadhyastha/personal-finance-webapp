# ===================================================================
# IMPORTS (CONSOLIDATED AND FINAL)
# ===================================================================
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    jsonify,
    Response,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from . import db, bcrypt
import decimal
import csv
import secrets
import io
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from .models import (
    Transaction,
    User,
    Category,
    Account,
    Budget,
    Tag,
    transaction_categories,
    RecurringTransaction,
    ActivityLog,
    Asset,
    InvestmentTransaction,
)
from sqlalchemy import func, select, or_, text, case
from sqlalchemy.orm import selectinload
import calendar
from dateutil.relativedelta import relativedelta
from .forms import TransactionForm
from .services import get_stock_price
import codecs
from azure.storage.blob import BlobServiceClient, ContentSettings
from werkzeug.utils import secure_filename
import mimetypes
import os
from functools import wraps
from flask import abort
from .utils import process_tags, parse_date_range
import re

# ===================================================================
# BLUEPRINT DEFINITION
# ===================================================================
main_bp = Blueprint("main", __name__)


# ===================================================================
# HELPER FUNCTION
# ===================================================================
def log_activity(description):
    """Helper function to create an ActivityLog entry for the current user."""
    if current_user.is_authenticated:
        log_entry = ActivityLog(user_id=current_user.id, description=description)
        db.session.add(log_entry)


@main_bp.route("/healthz")
def healthz():
    """
    A simple health check endpoint. It checks for a valid database connection.
    Returns a 200 OK if healthy, and a 503 Service Unavailable if not.
    """
    try:
        # Perform a very simple, fast query to check DB connectivity.
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        # If any exception occurs, it means the app is not healthy.
        # Log the error for debugging purposes.
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({"status": "database_error"}), 503


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden error
        return f(*args, **kwargs)

    return decorated_function


# ===================================================================
# CORE & DASHBOARD ROUTES
# ===================================================================
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main_bp.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    """
    Displays an admin-only dashboard with system-wide statistics
    and a list of all registered users.
    """
    # --- NEW: System-wide Statistics ---

    # Get total counts for users and transactions
    user_count = db.session.query(func.count(User.id)).scalar()
    transaction_count = db.session.query(func.count(Transaction.id)).scalar()

    # Get the sum of all income and expense transactions in a single query
    totals_query = (
        db.session.query(Transaction.transaction_type, func.sum(Transaction.amount))
        .group_by(Transaction.transaction_type)
        .all()
    )

    # Process the results into a simple dictionary
    # Initialize with 0 to handle cases where there are no transactions of a certain type
    system_totals = {
        "income": decimal.Decimal("0.0"),
        "expense": decimal.Decimal("0.0"),
    }
    for trans_type, total_amount in totals_query:
        if trans_type in system_totals:
            system_totals[trans_type] = total_amount

    # --- Existing logic to get all users ---
    stmt = select(User).order_by(User.username)
    all_users = db.session.execute(stmt).scalars().all()

    # --- Pass all data to the template ---
    return render_template(
        "admin_dashboard.html",
        users=all_users,
        user_count=user_count,
        transaction_count=transaction_count,
        total_income=system_totals["income"],
        total_expenses=system_totals["expense"],
    )


@main_bp.route("/admin/user/promote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id):
    """Promotes a regular user to become an administrator."""
    if user_id == current_user.id:
        flash("You cannot change your own admin status.", "danger")
        return redirect(url_for("main.admin_dashboard"))

    user_to_promote = db.get_or_404(User, user_id)
    user_to_promote.is_admin = True
    db.session.commit()

    log_activity(f"Promoted user '{user_to_promote.username}' to admin.")
    flash(
        f"User '{user_to_promote.username}' has been promoted to an admin.", "success"
    )
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/user/demote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def demote_user(user_id):
    """Demotes an administrator back to a regular user."""
    if user_id == current_user.id:
        flash("You cannot change your own admin status.", "danger")
        return redirect(url_for("main.admin_dashboard"))

    user_to_demote = db.get_or_404(User, user_id)
    user_to_demote.is_admin = False
    db.session.commit()

    log_activity(f"Demoted admin '{user_to_demote.username}' to regular user.")
    flash(
        f"User '{user_to_demote.username}' has been demoted to a regular user.", "info"
    )
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # --- Date Range Handling for Charts & Summary Cards ---
    start_date, end_date, start_date_str, end_date_str = parse_date_range(request.args)
    end_date_inclusive = datetime.combine(end_date, datetime.max.time())

    # --- Calculate Summary Totals for the Selected Period ---
    summary_stmt = (
        select(Transaction.transaction_type, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date.between(start_date, end_date_inclusive),
            Transaction.affects_balance == True,
        )
        .group_by(Transaction.transaction_type)
    )

    summary_data = {row[0]: row[1] for row in db.session.execute(summary_stmt).all()}
    total_income = summary_data.get("income", decimal.Decimal(0))
    total_expenses = summary_data.get("expense", decimal.Decimal(0))
    net_balance = total_income - total_expenses

    # --- Fetch Data for Tables and Feeds ---
    accounts_stmt = select(Account).filter_by(user_id=current_user.id)
    user_accounts = db.session.execute(accounts_stmt).scalars().all()

    trans_stmt = (
        select(Transaction)
        .options(selectinload(Transaction.categories), selectinload(Transaction.tags))
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.transaction_date.desc())
        .limit(10)
    )
    recent_transactions = db.session.execute(trans_stmt).scalars().all()

    activity_logs_stmt = (
        select(ActivityLog)
        .filter_by(user_id=current_user.id)
        .order_by(ActivityLog.timestamp.desc())
        .limit(5)
    )
    recent_activity = db.session.execute(activity_logs_stmt).scalars().all()

    now_utc = datetime.now(timezone.utc)
    current_month = now_utc.month
    current_year = now_utc.year

    current_budgets_stmt = select(Budget).filter_by(
        user_id=current_user.id, month=current_month, year=current_year
    )
    current_budgets = db.session.execute(current_budgets_stmt).scalars().all()

    expenses_by_category_stmt = (
        select(transaction_categories.c.category_id, func.sum(Transaction.amount))
        .join(Transaction, Transaction.id == transaction_categories.c.transaction_id)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            func.extract("month", Transaction.transaction_date) == current_month,
            func.extract("year", Transaction.transaction_date) == current_year,
            Transaction.affects_balance == True,
        )
        .group_by(transaction_categories.c.category_id)
    )

    spending_by_category = {
        row[0]: row[1] for row in db.session.execute(expenses_by_category_stmt).all()
    }

    budget_progress_data = []
    for budget in current_budgets:
        total_spent = spending_by_category.get(budget.category_id, decimal.Decimal(0))
        percentage_used = (
            (total_spent / budget.amount) * 100 if budget.amount > 0 else 0
        )

        # Calculate the final values to be used directly in the template
        width_percent = min(percentage_used, 100)
        color_hex = "#1095c1"  # Default blue
        if percentage_used >= 100:
            color_hex = "#d92121"  # Red
        elif percentage_used > 85:
            color_hex = "#ffb700"  # Yellow/Amber

        budget_progress_data.append(
            {
                "category_name": budget.category.name,
                "budget_limit": budget.amount,
                "total_spent": total_spent,
                "percentage_used": percentage_used,
                "width": width_percent,
                "color": color_hex,
            }
        )

    # --- Final Render with ALL Data ---
    return render_template(
        "dashboard.html",
        accounts=user_accounts,
        transactions=recent_transactions,
        budget_progress=budget_progress_data,
        activity_logs=recent_activity,
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=net_balance,
        start_date=start_date_str,
        end_date=end_date_str,
    )


# ===================================================================
# TRANSACTION CRUD
# ===================================================================
@main_bp.route("/transactions")
@login_required
def transactions():
    page = request.args.get("page", 1, type=int)
    # Get all potential filters from the URL query parameters
    search_query = request.args.get("q", "").strip()
    trans_type = request.args.get("type", "").strip()
    # --- NEW: Get account and category filters ---
    account_id = request.args.get("account_id", type=int)
    category_id = request.args.get("category_id", type=int)
    # --- END NEW ---
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # Start with a base query and eagerly load related data
    stmt = (
        select(Transaction)
        .options(
            selectinload(Transaction.account),
            selectinload(Transaction.categories),
            selectinload(Transaction.tags),
        )
        .filter_by(user_id=current_user.id)
    )

    # --- Apply Filters Dynamically ---
    if trans_type in ["income", "expense"]:
        stmt = stmt.where(Transaction.transaction_type == trans_type)

    # --- NEW: Filter by account ---
    if account_id:
        stmt = stmt.where(Transaction.account_id == account_id)
    # --- END NEW ---

    # --- NEW: Filter by category ---
    if category_id:
        # This checks if the transaction is associated with the given category ID
        stmt = stmt.where(Transaction.categories.any(id=category_id))
    # --- END NEW ---

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            end_date_inclusive = datetime.combine(end_date, datetime.max.time())
            stmt = stmt.where(
                Transaction.transaction_date.between(start_date, end_date_inclusive)
            )
        except ValueError:
            flash("Invalid date format provided.", "error")
            start_date_str, end_date_str = None, None

    if search_query:
        search_term = f"%{search_query}%"
        stmt = (
            stmt.join(Transaction.categories, isouter=True)
            .join(Transaction.tags, isouter=True)
            .filter(
                or_(
                    Transaction.description.ilike(search_term),
                    Transaction.notes.ilike(search_term),
                    Category.name.ilike(search_term),
                    Tag.name.ilike(search_term),
                )
            )
            .distinct()
        )

    # --- Finalize and Execute Query ---
    stmt = stmt.order_by(Transaction.transaction_date.desc())
    all_transactions = db.paginate(stmt, page=page, per_page=15, error_out=False)

    # --- NEW: Fetch accounts and categories for the filter dropdowns ---
    user_accounts = (
        db.session.execute(
            select(Account).filter_by(user_id=current_user.id).order_by(Account.name)
        )
        .scalars()
        .all()
    )
    user_categories = (
        db.session.execute(
            select(Category).filter_by(user_id=current_user.id).order_by(Category.name)
        )
        .scalars()
        .all()
    )
    # --- END NEW ---

    return render_template(
        "transactions.html",
        transactions=all_transactions,
        # Pass all filters back to the template
        search_query=search_query,
        selected_type=trans_type,
        start_date=start_date_str,
        end_date=end_date_str,
        # --- NEW: Pass new data to the template ---
        accounts=user_accounts,
        categories=user_categories,
        selected_account_id=account_id,
        selected_category_id=category_id,
        # --- END NEW ---
    )


@main_bp.route("/add_transaction", methods=["GET", "POST"])
@login_required
def add_transaction():
    if not db.session.execute(
        select(Account).filter_by(user_id=current_user.id)
    ).first():
        flash("You must create an account before adding a transaction.", "warning")
        return redirect(url_for("main.add_account"))

    form = TransactionForm()

    if form.validate_on_submit():
        new_transaction = Transaction(
            description=form.description.data,
            amount=form.amount.data,
            transaction_type=form.transaction_type.data,
            notes=form.notes.data,
            user_id=current_user.id,
            account_id=form.account.data.id,
            transaction_date=form.transaction_date.data,
            affects_balance=(
                form.affects_balance.data
                if form.transaction_type.data == "expense"
                else True
            ),
        )

        # --- THIS IS THE FIX ---
        # The balance is now updated only once, correctly respecting the flag.
        if new_transaction.affects_balance:
            account = form.account.data
            if new_transaction.transaction_type == "income":
                account.balance += new_transaction.amount
            else:
                account.balance -= new_transaction.amount
        # --- END OF FIX ---

        if form.category.data:
            new_transaction.categories.append(form.category.data)

        process_tags(new_transaction, form.tags.data)

        db.session.add(new_transaction)
        log_activity(f"Added transaction: '{new_transaction.description}'")
        db.session.commit()

        flash("Transaction added successfully!", "success")
        return redirect(url_for("main.dashboard"))

    # For a GET request, pre-fill the date/time with the current time
    if request.method == "GET":
        form.transaction_date.data = datetime.now(timezone.utc)

    return render_template(
        "add_edit_transaction.html", form=form, title="Add Transaction"
    )


@main_bp.route("/edit_transaction/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    transaction = db.get_or_404(Transaction, transaction_id)
    if transaction.user_id != current_user.id:
        abort(403)

    # Store the transaction's original state before any changes are made.
    original_amount = transaction.amount
    original_type = transaction.transaction_type
    original_affects_balance = transaction.affects_balance
    original_account = transaction.account

    form = TransactionForm(obj=transaction)
    # Your logic to populate form choices for account/category is correct

    if form.validate_on_submit():
        # --- THIS IS THE CORRECTED, ROBUST BALANCE LOGIC ---

        # 1. Revert the effect of the original transaction IF it affected the balance.
        if original_affects_balance and original_account:
            if original_type == "income":
                original_account.balance -= original_amount
            else:  # expense
                original_account.balance += original_amount

        # 2. Update the transaction object with all the new data from the form.
        transaction.description = form.description.data
        transaction.amount = form.amount.data
        transaction.transaction_type = form.transaction_type.data
        transaction.transaction_date = form.transaction_date.data
        transaction.notes = form.notes.data
        transaction.account_id = form.account.data.id
        # Set affects_balance based on the form, only if it's an expense.
        transaction.affects_balance = (
            form.affects_balance.data
            if form.transaction_type.data == "expense"
            else True
        )

        # 3. Apply the effect of the NEW transaction state to the (potentially new) account.
        new_account = db.session.get(Account, form.account.data.id)
        if transaction.affects_balance and new_account:
            if transaction.transaction_type == "income":
                new_account.balance += transaction.amount
            else:  # expense
                new_account.balance -= transaction.amount
        # --- END OF CORRECTED LOGIC ---

        # Update relationships
        process_tags(transaction, form.tags.data)  # This helper handles tags correctly
        transaction.categories.clear()
        if form.category.data:
            transaction.categories.append(form.category.data)

        log_activity(f"Updated transaction: '{transaction.description}'")
        db.session.commit()
        flash("Transaction updated successfully!", "success")
        return redirect(url_for("main.transactions"))

    # Pre-populate the form for the GET request
    if request.method == "GET":
        form.account.data = transaction.account
        if transaction.categories:
            form.category.data = transaction.categories[0]
        form.tags.data = ", ".join([tag.name for tag in transaction.tags])
        form.transaction_date.data = transaction.transaction_date
        # Pre-populate the checkbox
        form.affects_balance.data = transaction.affects_balance

    return render_template(
        "add_edit_transaction.html", form=form, title="Edit Transaction"
    )


@main_bp.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    if not transaction:
        abort(404)
    if transaction.user_id != current_user.id:
        abort(403)

    log_activity(
        f"Deleted transaction: '{transaction.description}' (₹{transaction.amount:.2f})"
    )

    account = transaction.account
    if account:
        if transaction.transaction_type == "income":
            account.balance -= transaction.amount
        else:
            account.balance += transaction.amount

    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted successfully!", "success")
    return redirect(url_for("main.transactions"))


@main_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    """Handles transfers of funds between a user's own accounts."""
    # Fetch user's accounts first to check if a transfer is possible
    accounts = (
        db.session.execute(select(Account).filter_by(user_id=current_user.id))
        .scalars()
        .all()
    )

    # If the user has fewer than 2 accounts, we don't even need to check for a POST.
    # We just render the page in its "error" state.
    if len(accounts) < 2:
        # We don't need a flash message anymore because the template will handle it.
        return render_template("transfer_form.html", accounts=accounts)

    if request.method == "POST":
        # ... (Your existing POST logic is correct and does not need to change) ...
        # ... it handles the form submission, validation, and transfer ...
        from_account_id = request.form.get("from_account_id")
        to_account_id = request.form.get("to_account_id")
        amount_str = request.form.get("amount")

        if not all([from_account_id, to_account_id, amount_str]):
            flash("All fields are required.", "error")
            return redirect(url_for("main.transfer"))

        if from_account_id == to_account_id:
            flash('"From" and "To" accounts cannot be the same.', "error")
            return redirect(url_for("main.transfer"))

        try:
            amount = decimal.Decimal(amount_str)
            if amount <= 0:
                flash("Transfer amount must be positive.", "error")
                return redirect(url_for("main.transfer"))

            from_account = db.session.get(Account, int(from_account_id))
            to_account = db.session.get(Account, int(to_account_id))

            if (
                not from_account
                or from_account.user_id != current_user.id
                or not to_account
                or to_account.user_id != current_user.id
            ):
                abort(403)

            now = datetime.now(timezone.utc)
            expense_trans = Transaction(
                description=f"Transfer to {to_account.name}",
                amount=amount,
                transaction_type="expense",
                transaction_date=now,
                user_id=current_user.id,
                account_id=from_account.id,
            )
            income_trans = Transaction(
                description=f"Transfer from {from_account.name}",
                amount=amount,
                transaction_type="income",
                transaction_date=now,
                user_id=current_user.id,
                account_id=to_account.id,
            )

            from_account.balance -= amount
            to_account.balance += amount

            db.session.add_all([expense_trans, income_trans])
            log_activity(
                f"Transferred ₹{amount:.2f} from '{from_account.name}' to '{to_account.name}'."
            )
            db.session.commit()

            flash("Transfer completed successfully!", "success")
            return redirect(url_for("main.dashboard"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Transfer failed: {e}")
            flash(
                "An unexpected error occurred. The transfer was not completed.",
                "danger",
            )
            return redirect(url_for("main.transfer"))

    # For a GET request (when the user has enough accounts), show the form.
    return render_template("transfer_form.html", accounts=accounts)


@main_bp.route("/import", methods=["GET", "POST"])
@login_required
def import_transactions():
    if request.method == "POST":
        if (
            "transaction_file" not in request.files
            or not request.files["transaction_file"].filename
        ):
            flash("No file selected.", "warning")
            return redirect(request.url)

        file = request.files["transaction_file"]
        if not file.filename.endswith(".csv"):
            flash("Invalid file type. Please upload a .csv file.", "danger")
            return redirect(request.url)

        try:
            stream = codecs.iterdecode(file.stream, "utf-8")
            csv_reader = csv.reader(stream)
            header = next(csv_reader)  # Skip header row

            transactions_to_add, accounts_to_update, errors = [], {}, []
            success_count = 0

            user_accounts = {
                (acc.name.lower(), acc.account_type.lower()): acc
                for acc in db.session.execute(
                    select(Account).filter_by(user_id=current_user.id)
                ).scalars()
            }
            user_categories = {
                cat.name.lower(): cat
                for cat in db.session.execute(
                    select(Category).filter_by(user_id=current_user.id)
                ).scalars()
            }
            user_tags = {
                tag.name.lower(): tag
                for tag in db.session.execute(
                    select(Tag).filter_by(user_id=current_user.id)
                ).scalars()
            }

            for i, row in enumerate(csv_reader):
                row_num = i + 2

                # --- THIS IS THE CORRECTED UNPACKING AND PARSING LOGIC ---
                try:
                    # 1. Unpack the 10 columns from the CSV row
                    (
                        date_str,
                        time_str,
                        desc,
                        amount_str,
                        dr_cr_str,
                        account_str,
                        is_expense_str,
                        cats_str,
                        tags_str,
                        notes,
                    ) = row
                except ValueError:
                    errors.append(
                        f"Row {row_num}: Invalid number of columns. Expected 10, got {len(row)}."
                    )
                    continue

                dr_cr = dr_cr_str.strip().upper()
                if dr_cr not in ["DR", "CR"]:
                    errors.append(f"Row {row_num}: DR/CR column must be 'DR' or 'CR'.")
                    continue

                # 2. Parse Date, Time, and Amount
                try:
                    combined_datetime_str = f"{date_str.strip()} {time_str.strip()}"
                    trans_date = datetime.strptime(
                        combined_datetime_str, "%Y-%m-%d %I:%M %p"
                    )
                    amount = decimal.Decimal(amount_str)
                except (ValueError, decimal.InvalidOperation):
                    errors.append(
                        f"Row {row_num}: Invalid date/time ('{date_str} {time_str}') or amount ('{amount_str}')."
                    )
                    continue

                # 3. Derive internal values from CSV strings
                trans_type = "expense" if dr_cr == "DR" else "income"
                affects_balance = True  # Default to true
                if trans_type == "expense" and is_expense_str.strip().lower() == "no":
                    affects_balance = False

                # 4. Parse the combined Account string using Regex
                acc_name, acc_type = None, None
                match = re.match(r"^(.*) \((.*)\)$", account_str.strip())
                if match:
                    acc_name, acc_type = match.groups()
                else:
                    errors.append(
                        f"Row {row_num}: Could not parse account format '{account_str}'. Expected 'Name (Type)'."
                    )
                    continue
                # --- END OF CORRECTED LOGIC ---

                account = user_accounts.get((acc_name.lower(), acc_type.lower()))
                if not account:
                    errors.append(
                        f"Row {row_num}: Account '{acc_name}' ({acc_type}) not found."
                    )
                    continue

                # Prepare transaction
                new_trans = Transaction(
                    user_id=current_user.id,
                    transaction_date=trans_date,
                    description=desc.strip(),
                    amount=amount,
                    transaction_type=trans_type,
                    affects_balance=affects_balance,
                    account_id=account.id,
                    notes=notes.strip(),
                )

                # Process Categories
                if cats_str:
                    cat_names = [
                        name.strip() for name in cats_str.split(";") if name.strip()
                    ]
                    for cat_name in cat_names:
                        category = user_categories.get(cat_name.lower())
                        if not category:
                            category = Category(name=cat_name, user_id=current_user.id)
                            db.session.add(category)
                            user_categories[cat_name.lower()] = category
                        new_trans.categories.append(category)

                # Process Tags
                if tags_str:
                    tag_names = [
                        name.strip() for name in tags_str.split(";") if name.strip()
                    ]
                    for tag_name in tag_names:
                        tag = user_tags.get(tag_name.lower())
                        if not tag:
                            tag = Tag(name=tag_name, user_id=current_user.id)
                            db.session.add(tag)
                            user_tags[tag_name.lower()] = tag
                        new_trans.tags.append(tag)

                transactions_to_add.append(new_trans)

                # Update balance only if the flag is set
                if affects_balance:
                    balance_change = amount if trans_type == "income" else -amount
                    if account.id not in accounts_to_update:
                        accounts_to_update[account.id] = {
                            "account": account,
                            "change": decimal.Decimal(0),
                        }
                    accounts_to_update[account.id]["change"] += balance_change

                success_count += 1

            # Atomic Database Operation
            if transactions_to_add:
                db.session.add_all(transactions_to_add)
                for data in accounts_to_update.values():
                    data["account"].balance += data["change"]
                db.session.commit()
                flash(f"Successfully imported {success_count} transactions.", "success")

            if errors:
                flash("Some rows were skipped due to errors:", "warning")
                for error in errors[:5]:
                    flash(error, "danger")

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {e}", "danger")
            current_app.logger.error(f"CSV Import failed: {e}")

        return redirect(url_for("main.transactions"))

    return render_template("import.html")


@main_bp.route("/api/import/validate", methods=["POST"])
@login_required
def validate_import_file():
    """
    Analyzes an uploaded CSV file for common errors and returns a
    structured JSON report without actually importing the data.
    This version matches the final 10-column import format.
    """
    if (
        "transaction_file" not in request.files
        or not request.files["transaction_file"].filename
    ):
        return jsonify({"error": "No file selected."}), 400

    file = request.files["transaction_file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file type. Please upload a .csv file."}), 400

    validation_report = {
        "valid_rows": [],
        "invalid_rows": [],
        "summary": {"total_rows": 0, "valid_count": 0, "invalid_count": 0},
    }

    try:
        # Pre-fetch user's accounts for efficient lookups
        user_accounts = {
            (acc.name.lower(), acc.account_type.lower()): acc
            for acc in db.session.execute(
                select(Account).filter_by(user_id=current_user.id)
            ).scalars()
        }

        stream = codecs.iterdecode(file.stream, "utf-8")
        csv_reader = csv.reader(stream)

        try:
            header = next(csv_reader)
        except StopIteration:
            return jsonify({"error": "CSV file is empty or missing a header."}), 400

        for i, row in enumerate(csv_reader):
            row_num = i + 2
            errors = []
            validation_report["summary"]["total_rows"] += 1
            if not any(field.strip() for field in row):
                continue

            # 1. Check for the correct 10-column format
            if len(row) != 10:
                errors.append(f"Invalid column count. Expected 10, got {len(row)}.")
                validation_report["invalid_rows"].append(
                    {"row_number": row_num, "data": row, "errors": errors}
                )
                validation_report["summary"]["invalid_count"] += 1
                continue

            (
                date_str,
                time_str,
                desc,
                amount_str,
                dr_cr_str,
                account_str,
                is_expense_str,
                cats_str,
                tags_str,
                notes,
            ) = row
            dr_cr = dr_cr_str.strip().upper()
            # 2. Validate date, time, and amount
            try:
                datetime.strptime(
                    f"{date_str.strip()} {time_str.strip()}", "%Y-%m-%d %I:%M %p"
                )
                decimal.Decimal(amount_str)
            except (ValueError, decimal.InvalidOperation):
                errors.append(
                    f"Invalid date/time ('{date_str} {time_str}') or amount ('{amount_str}')."
                )

            # 3. Validate DR/CR column
            is_expense_val = is_expense_str.strip().lower()
            if dr_cr == "DR" and is_expense_val not in ["yes", "no", ""]:
                errors.append(f"'Is Expense?' must be 'Yes', 'No', or empty.")

            # 4. Validate that the account can be parsed and exists
            acc_name, acc_type = None, None
            match = re.match(r"^(.*) \((.*)\)$", account_str.strip())
            if match:
                acc_name, acc_type = match.groups()
                if not user_accounts.get((acc_name.lower(), acc_type.lower())):
                    errors.append(f"Account '{acc_name}' ({acc_type}) not found.")
            else:
                errors.append(
                    f"Could not parse account format '{account_str}'. Expected 'Name (Type)'."
                )

            # Finalize row validation
            if errors:
                validation_report["invalid_rows"].append(
                    {"row_number": row_num, "data": row, "errors": errors}
                )
                validation_report["summary"]["invalid_count"] += 1
            else:
                validation_report["valid_rows"].append(
                    {"row_number": row_num, "data": row}
                )
                validation_report["summary"]["valid_count"] += 1

        return jsonify(validation_report)

    except Exception as e:
        current_app.logger.error(f"CSV Validation failed: {e}")
        return (
            jsonify({"error": "An unexpected error occurred during file validation."}),
            500,
        )


@main_bp.route("/api/import/commit", methods=["POST"])
@login_required
def commit_import_data():
    """
    Receives a finalized JSON payload of transaction data, creates the
    transaction records, and commits them to the database.
    """
    final_data = request.get_json()
    if not final_data or "transactions" not in final_data:
        return jsonify({"error": "Invalid or missing JSON payload."}), 400

    transactions_to_import = final_data["transactions"]

    try:
        # This logic is very similar to your original import function
        transactions_to_add, accounts_to_update = [], {}
        user_accounts = {
            (acc.name.lower(), acc.account_type.lower()): acc
            for acc in db.session.execute(
                select(Account).filter_by(user_id=current_user.id)
            ).scalars()
        }
        user_categories = {
            cat.name.lower(): cat
            for cat in db.session.execute(
                select(Category).filter_by(user_id=current_user.id)
            ).scalars()
        }
        user_tags = {
            tag.name.lower(): tag
            for tag in db.session.execute(
                select(Tag).filter_by(user_id=current_user.id)
            ).scalars()
        }

        for row_data in transactions_to_import:
            # Unpack the row data
            (
                date_str,
                time_str,
                desc,
                amount_str,
                dr_cr_str,
                account_str,
                is_expense_str,
                cats_str,
                tags_str,
                notes,
            ) = row_data

            # This block assumes data is already validated, but we perform light parsing
            trans_date = datetime.strptime(
                f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p"
            )
            amount = decimal.Decimal(amount_str)
            trans_type = "expense" if dr_cr_str.upper() == "DR" else "income"
            affects_balance = (
                False
                if trans_type == "expense" and is_expense_str.lower() == "no"
                else True
            )

            # Parse account
            acc_name, acc_type = None, None
            match = re.match(r"^(.*) \((.*)\)$", account_str.strip())
            if match:
                acc_name, acc_type = match.groups()

            account = user_accounts.get((acc_name.lower(), acc_type.lower()))
            if not account:
                continue  # Skip if account not found (should not happen with validated data)

            # Create the transaction object
            new_trans = Transaction(
                user_id=current_user.id,
                transaction_date=trans_date,
                description=desc,
                amount=amount,
                transaction_type=trans_type,
                affects_balance=affects_balance,
                account_id=account.id,
                notes=notes,
            )

            # Process Categories and Tags
            if cats_str:
                for cat_name in [c.strip() for c in cats_str.split(";") if c.strip()]:
                    category = user_categories.get(cat_name.lower())
                    if not category:
                        category = Category(name=cat_name, user_id=current_user.id)
                        db.session.add(category)
                        user_categories[cat_name.lower()] = category
                    new_trans.categories.append(category)

            if tags_str:
                for tag_name in [t.strip() for t in tags_str.split(";") if t.strip()]:
                    tag = user_tags.get(tag_name.lower())
                    if not tag:
                        tag = Tag(name=tag_name, user_id=current_user.id)
                        db.session.add(tag)
                        user_tags[tag_name.lower()] = tag
                    new_trans.tags.append(tag)

            transactions_to_add.append(new_trans)

            # Tally balance changes
            if affects_balance:
                balance_change = amount if trans_type == "income" else -amount
                if account.id not in accounts_to_update:
                    accounts_to_update[account.id] = {
                        "account": account,
                        "change": decimal.Decimal(0),
                    }
                accounts_to_update[account.id]["change"] += balance_change

        # Final atomic commit
        if transactions_to_add:
            db.session.add_all(transactions_to_add)
            for data in accounts_to_update.values():
                data["account"].balance += data["change"]
            db.session.commit()

        return (
            jsonify(
                {
                    "message": f"Successfully imported {len(transactions_to_import)} transactions."
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Final CSV Commit failed: {e}")
        return (
            jsonify({"error": "An unexpected error occurred during the final import."}),
            500,
        )


# ===================================================================
# ACCOUNT & BUDGET ROUTES
# ===================================================================


@main_bp.route("/accounts")
@login_required
def accounts():
    """
    Fetches and displays a list of all financial accounts for the current user.
    """
    user_accounts = (
        db.session.execute(
            select(Account).filter_by(user_id=current_user.id).order_by(Account.name)
        )
        .scalars()
        .all()
    )

    return render_template("accounts.html", accounts=user_accounts)


@main_bp.route("/account/<int:account_id>")
@login_required
def account_detail(account_id):
    account = db.session.get(Account, account_id)
    if not account:
        abort(404)
    if account.user_id != current_user.id:
        abort(403)

    stmt = (
        select(Transaction)
        .filter_by(account_id=account.id)
        .order_by(Transaction.transaction_date.desc())
    )
    transactions = db.session.execute(stmt).scalars().all()

    return render_template(
        "account_detail.html", account=account, transactions=transactions
    )


@main_bp.route("/add_account", methods=["GET", "POST"])
@login_required
def add_account():
    if request.method == "POST":
        name = request.form.get("name")
        acc_type = request.form.get("account_type")
        balance = request.form.get("balance", 0)
        new_account = Account(
            name=name, account_type=acc_type, balance=balance, user_id=current_user.id
        )
        db.session.add(new_account)
        log_activity(f"Created new account: '{new_account.name}'")
        db.session.commit()
        flash("Account created successfully!", "success")
        return redirect(url_for("main.accounts"))

    return render_template("add_account.html")


@main_bp.route("/edit_account/<int:account_id>", methods=["GET", "POST"])
@login_required
def edit_account(account_id):
    account = db.session.get(Account, account_id)
    if not account:
        abort(404)
    if account.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        account.name = request.form.get("name")
        account.account_type = request.form.get("account_type")
        db.session.commit()
        flash("Account updated successfully!", "success")
        return redirect(url_for("main.accounts"))

    return render_template("edit_account.html", account=account)


@main_bp.route("/delete_account/<int:account_id>", methods=["POST"])
@login_required
def delete_account(account_id):
    account = db.session.get(Account, account_id)
    if not account:
        abort(404)
    if account.user_id != current_user.id:
        abort(403)

    if account.transactions:
        flash("Cannot delete account with transactions.", "error")
        return redirect(url_for("main.accounts"))

    db.session.delete(account)
    db.session.commit()
    flash("Account deleted successfully!", "success")
    return redirect(url_for("main.accounts"))


@main_bp.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    if request.method == "POST":
        category_id = request.form.get("category_id")
        amount = request.form.get("amount")
        month = request.form.get("month")
        year = request.form.get("year")

        if not all([category_id, amount, month, year]):
            flash("All fields are required.", "error")
            return redirect(url_for("main.budgets"))

        stmt = select(Budget).filter_by(
            user_id=current_user.id,
            category_id=int(category_id),
            month=int(month),
            year=int(year),
        )
        existing_budget = db.session.execute(stmt).scalar_one_or_none()

        if existing_budget:
            flash("A budget for this category and month already exists.", "warning")
        else:
            new_budget = Budget(
                user_id=current_user.id,
                category_id=int(category_id),
                amount=decimal.Decimal(amount),
                month=int(month),
                year=int(year),
            )
            db.session.add(new_budget)
            db.session.commit()
            flash("Budget created successfully!", "success")

        return redirect(url_for("main.budgets"))

    user_budgets = (
        db.session.execute(
            select(Budget)
            .filter_by(user_id=current_user.id)
            .order_by(Budget.year.desc(), Budget.month.desc())
        )
        .scalars()
        .all()
    )
    user_categories = (
        db.session.execute(
            select(Category).filter_by(user_id=current_user.id).order_by(Category.name)
        )
        .scalars()
        .all()
    )

    current_year = datetime.now(timezone.utc).year
    years_for_dropdown = range(current_year - 1, current_year + 5)
    month_names = {i: datetime(current_year, i, 1).strftime("%B") for i in range(1, 13)}

    return render_template(
        "budgets.html",
        budgets=user_budgets,
        categories=user_categories,
        years=years_for_dropdown,
        month_names=month_names,
    )


@main_bp.route("/edit_budget/<int:budget_id>", methods=["GET", "POST"])
@login_required
def edit_budget(budget_id):
    """Handles editing an existing budget."""
    budget = db.session.get(Budget, budget_id)
    if not budget:
        abort(404)
    if budget.user_id != current_user.id:
        abort(403)  # Forbidden

    if request.method == "POST":
        new_amount = request.form.get("amount")
        # You could add logic here to allow changing month/year/category if desired,
        # but for simplicity, we'll focus on updating the amount.
        if new_amount:
            budget.amount = decimal.Decimal(new_amount)
            db.session.commit()
            flash("Budget updated successfully!", "success")
            return redirect(url_for("main.budgets"))
        else:
            flash("Amount cannot be empty.", "error")

    # For a GET request, pass the necessary data to the template
    current_year = datetime.utcnow().year
    years_for_dropdown = range(current_year - 1, current_year + 5)
    month_names = {i: datetime(current_year, i, 1).strftime("%B") for i in range(1, 13)}

    return render_template(
        "edit_budget.html",
        budget=budget,
        years=years_for_dropdown,
        month_names=month_names,
    )


@main_bp.route("/delete_budget/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    """Handles deleting a budget."""
    budget = db.session.get(Budget, budget_id)
    if not budget:
        abort(404)
    if budget.user_id != current_user.id:
        abort(403)

    db.session.delete(budget)
    db.session.commit()
    flash("Budget deleted successfully!", "success")
    return redirect(url_for("main.budgets"))


# ===================================================================
# CATEGORY, PROFILE & AUTH ROUTES
# ===================================================================


@main_bp.route("/categories", methods=["GET", "POST"])
@login_required
def manage_categories():
    if request.method == "POST":
        name = request.form.get("name")
        if name:
            stmt = select(Category).filter(
                func.lower(Category.name) == func.lower(name),
                Category.user_id == current_user.id,
            )
            existing_category = db.session.execute(stmt).scalar_one_or_none()
            if not existing_category:
                new_category = Category(name=name, user_id=current_user.id)
                db.session.add(new_category)
                db.session.commit()
                flash("Category added successfully!", "success")
            else:
                flash("A category with that name already exists.", "warning")
        else:
            flash("Category name cannot be empty.", "error")
        return redirect(url_for("main.manage_categories"))

    categories = (
        db.session.execute(
            select(Category).filter_by(user_id=current_user.id).order_by(Category.name)
        )
        .scalars()
        .all()
    )
    return render_template("categories.html", categories=categories)


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        # Check which form was submitted based on the button's 'name' and 'value'
        action = request.form.get("action")

        if action == "update_profile":
            new_email = request.form.get("email").strip()

            # Validation: Check if the new email is already taken by another user
            stmt = select(User).where(User.email == new_email)
            existing_user = db.session.execute(stmt).scalar_one_or_none()

            if existing_user and existing_user.id != current_user.id:
                flash(
                    "That email address is already in use by another account.", "error"
                )
            elif not new_email:
                flash("Email address cannot be empty.", "error")
            else:
                current_user.email = new_email
                db.session.commit()
                flash("Your profile has been updated successfully!", "success")

        elif action == "change_password":
            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            confirm_new_password = request.form.get("confirm_new_password")

            if not bcrypt.check_password_hash(
                current_user.password_hash, current_password
            ):
                flash("Your current password was incorrect. Please try again.", "error")
            elif new_password != confirm_new_password:
                flash("The new passwords do not match.", "error")
            else:
                current_user.password_hash = bcrypt.generate_password_hash(
                    new_password
                ).decode("utf-8")
                db.session.commit()
                flash("Your password has been updated successfully!", "success")

        return redirect(url_for("main.profile"))

    # For a GET request, just render the page as usual
    return render_template("profile.html")


@main_bp.route("/profile/generate-api-key", methods=["POST"])
@login_required
def generate_api_key():
    """Generates a new, secure API key for the current user."""

    # Generate a cryptographically secure, 32-byte token, represented as a 64-character hex string.
    new_key = secrets.token_hex(32)

    # Assign the new key to the user and save to the database
    current_user.api_key = new_key
    log_activity("Generated new API key.")
    db.session.commit()

    flash(
        "A new API key has been generated successfully. Your old key is now invalid.",
        "success",
    )
    return redirect(url_for("main.profile"))


@main_bp.route("/profile/delete", methods=["POST"])
@login_required
def delete_account_permanently():
    """Permanently deletes the current user and all their associated data."""

    # We get the user object for the logged-in user
    user_to_delete = db.session.get(User, current_user.id)

    if user_to_delete:
        # Log the user out first
        logout_user()

        # Delete the user object. The 'cascade' option will automatically
        # delete all associated transactions, accounts, budgets, etc.
        db.session.delete(user_to_delete)
        db.session.commit()

        flash(
            "Your account and all associated data have been permanently deleted.",
            "success",
        )

    # Redirect to the homepage after deletion
    return redirect(url_for("main.index"))


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # The existing checks for username and email are correct.
        if db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none():
            flash("Email address already in use.", "error")
        elif db.session.execute(
            select(User).filter_by(username=username)
        ).scalar_one_or_none():
            flash("Username already taken.", "error")
        else:
            # --- THIS IS THE FIX ---
            # We now generate a unique API key during registration.
            new_user = User(
                username=username,
                email=email,
                password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
                api_key=secrets.token_hex(32),  # Automatically generate a key
            )
            # --- END OF FIX ---

            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("main.login"))

    return render_template("register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.session.execute(
            select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("Login failed. Please check your email and password.", "error")
    return render_template("login.html")


@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/tag/<tag_name>")
@login_required
def tag_detail(tag_name):
    """Displays all transactions for a specific tag."""

    # Find the tag by name, ensuring it belongs to the current user for security.
    # We use a case-insensitive comparison for a better user experience.
    stmt = select(Tag).where(
        func.lower(Tag.name) == func.lower(tag_name), Tag.user_id == current_user.id
    )
    tag = db.session.execute(stmt).scalar_one_or_none()

    if not tag:
        # If the tag doesn't exist or doesn't belong to the user, return a 404.
        abort(404)

    # The backref 'tag.transactions' automatically gives us a list of all transactions
    # associated with this tag. We can sort this list directly.
    transactions = sorted(
        tag.transactions, key=lambda t: t.transaction_date, reverse=True
    )

    return render_template(
        "tag_detail.html", tag_name=tag.name, transactions=transactions
    )


@main_bp.route("/profile/avatar/upload", methods=["POST"])
@login_required
def upload_avatar():
    if "avatar" not in request.files or not request.files["avatar"].filename:
        flash("No file selected.", "warning")
        return redirect(url_for("main.profile"))

    file = request.files["avatar"]

    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        flash("Invalid file type. Please upload a PNG, JPG, or GIF.", "danger")
        return redirect(url_for("main.profile"))

    try:
        connection_string = current_app.config.get("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            flash("Storage service is not configured.", "danger")
            return redirect(url_for("main.profile"))

        file_content = file.read()
        filename = f"avatar_{current_user.id}{ext}"

        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        container_client = blob_service_client.get_container_client("avatars")
        blob_client = container_client.get_blob_client(filename)

        # Create a proper ContentSettings object
        content_settings = ContentSettings(
            content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )

        # Upload the raw bytes content
        blob_client.upload_blob(
            file_content,
            blob_type="BlockBlob",
            overwrite=True,
            content_settings=content_settings,
        )

        # Update the user's avatar URL
        current_user.avatar_url = blob_client.url
        log_activity("Updated profile picture.")
        db.session.commit()

        flash("Profile picture updated successfully!", "success")

    except Exception as e:
        # Log the actual error on the server for debugging, but show a generic message to the user.
        current_app.logger.error(
            f"Avatar upload failed for user {current_user.id}: {e}", exc_info=True
        )
        flash("There was an error uploading your file.", "danger")

    return redirect(url_for("main.profile"))


@main_bp.route("/portfolio")
@login_required
def portfolio():
    """
    Renders the main investment portfolio page, showing a summary of
    current holdings with live market values and a history of all transactions.
    """
    holdings_query = (
        db.session.query(
            Asset.ticker_symbol,
            func.sum(
                case(
                    (
                        InvestmentTransaction.transaction_type == "buy",
                        InvestmentTransaction.quantity,
                    ),
                    (
                        InvestmentTransaction.transaction_type == "sell",
                        -InvestmentTransaction.quantity,
                    ),
                    else_=0,
                )
            ).label("total_quantity"),
            func.sum(
                case(
                    (
                        InvestmentTransaction.transaction_type == "buy",
                        InvestmentTransaction.quantity
                        * InvestmentTransaction.price_per_unit,
                    ),
                    else_=0,
                )
            ).label("total_cost"),
        )
        .join(Asset, InvestmentTransaction.asset_id == Asset.id)
        .filter(InvestmentTransaction.user_id == current_user.id)
        .group_by(Asset.ticker_symbol)
        .all()
    )

    holdings_data = []
    # --- FIX: Use decimal.Decimal ---
    grand_total_cost = decimal.Decimal("0.0")
    grand_total_market_value = decimal.Decimal("0.0")

    from . import services

    if hasattr(services, "price_cache"):
        services.price_cache.clear()

    for holding in holdings_query:
        if holding.total_quantity > 0:
            ticker = holding.ticker_symbol

            # --- FIX: Use decimal.Decimal ---
            total_cost = holding.total_cost or decimal.Decimal("0.0")
            average_cost_per_share = (
                (total_cost / holding.total_quantity)
                if holding.total_quantity > 0
                else decimal.Decimal("0.0")
            )

            current_price_float = get_stock_price(ticker)

            market_value = None
            if current_price_float is not None:
                # --- FIX: Use decimal.Decimal ---
                current_price_decimal = decimal.Decimal(str(current_price_float))
                market_value = holding.total_quantity * current_price_decimal
                grand_total_market_value += market_value

            holdings_data.append(
                {
                    "ticker": ticker,
                    "quantity": holding.total_quantity,
                    "total_cost": total_cost,
                    "average_cost": average_cost_per_share,
                    "current_price": current_price_float,
                    "market_value": market_value,
                }
            )
            grand_total_cost += total_cost

    transaction_history = (
        db.session.execute(
            select(InvestmentTransaction)
            .options(selectinload(InvestmentTransaction.asset))
            .filter_by(user_id=current_user.id)
            .order_by(InvestmentTransaction.transaction_date.desc())
        )
        .scalars()
        .all()
    )

    return render_template(
        "portfolio.html",
        holdings=holdings_data,
        transactions=transaction_history,
        grand_total_cost=grand_total_cost,
        grand_total_market_value=grand_total_market_value,
    )


# ===================================================================
# API & REPORTING ROUTES
# ===================================================================


@main_bp.route("/calendar")
@login_required
def calendar_view():
    """Displays a monthly calendar highlighting days with transactions."""
    now_utc = datetime.now(timezone.utc)

    # Get month/year from query params, defaulting to the current month/year
    try:
        year = request.args.get("year", default=now_utc.year, type=int)
        month = request.args.get("month", default=now_utc.month, type=int)
        # Ensure month is valid
        if not (1 <= month <= 12):
            month = now_utc.month
    except (TypeError, ValueError):
        year = now_utc.year
        month = now_utc.month

    # 1. Get the calendar structure for the month (a list of weeks)
    cal = calendar.Calendar()
    month_calendar = cal.monthdayscalendar(year, month)

    # 2. Get a set of all days in this month that have transactions
    stmt = (
        select(func.extract("day", Transaction.transaction_date))
        .where(
            Transaction.user_id == current_user.id,
            func.extract("month", Transaction.transaction_date) == month,
            func.extract("year", Transaction.transaction_date) == year,
            Transaction.affects_balance == True,
        )
        .distinct()
    )

    active_days = {day[0] for day in db.session.execute(stmt).all()}

    # 3. Calculate previous and next month for navigation links
    current_date = datetime(year, month, 1)
    prev_month_date = current_date - relativedelta(months=1)
    next_month_date = current_date + relativedelta(months=1)

    prev_month_link = url_for(
        "main.calendar_view", year=prev_month_date.year, month=prev_month_date.month
    )
    next_month_link = url_for(
        "main.calendar_view", year=next_month_date.year, month=next_month_date.month
    )

    return render_template(
        "calendar.html",
        month_calendar=month_calendar,
        active_days=active_days,
        # Pass all the necessary date info to the template
        month_name=calendar.month_name[month],
        current_year=year,
        prev_month_link=url_for(
            "main.calendar_view", year=prev_month_date.year, month=prev_month_date.month
        ),
        next_month_link=url_for(
            "main.calendar_view", year=next_month_date.year, month=next_month_date.month
        ),
        prev_month_name=prev_month_date.strftime("%B"),
        next_month_name=next_month_date.strftime("%B"),
    )


@main_bp.route("/reports")
@login_required
def reports():
    stmt = (
        select(Transaction)
        .filter_by(user_id=current_user.id, transaction_type="expense")
        .order_by(Transaction.transaction_date.desc())
    )
    expenses = db.session.execute(stmt).scalars().all()

    monthly_summary_raw = defaultdict(lambda: defaultdict(float))
    for expense in expenses:
        month_key = expense.transaction_date.strftime("%Y-%m")
        if not expense.categories:
            monthly_summary_raw[month_key]["Uncategorized"] += float(expense.amount)
        else:
            for category in expense.categories:
                monthly_summary_raw[month_key][category.name] += float(expense.amount)

    monthly_summary_final = {}
    for month_key in sorted(monthly_summary_raw.keys(), reverse=True):
        month_name = datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")
        sorted_categories = sorted(
            monthly_summary_raw[month_key].items(),
            key=lambda item: item[1],
            reverse=True,
        )
        monthly_summary_final[month_name] = sorted_categories

    return render_template(
        "reports.html",
        monthly_summary=monthly_summary_final,
        now=datetime.now(timezone.utc),  # FIXED: Use timezone-aware datetime
    )


@main_bp.route("/report/yearly/<int:year>")
@login_required
def yearly_report(year):
    """
    Generates and displays a year-at-a-glance report showing total income,
    expenses, and net balance for each month.
    """
    # 1. The SQLAlchemy query to get monthly totals grouped by transaction type
    stmt = (
        select(
            func.extract("month", Transaction.transaction_date).label("month"),
            Transaction.transaction_type,
            func.sum(Transaction.amount).label("total_amount"),
        )
        .where(
            Transaction.user_id == current_user.id,
            func.extract("year", Transaction.transaction_date) == year,
            Transaction.affects_balance == True,
        )
        .group_by(
            func.extract("month", Transaction.transaction_date),
            Transaction.transaction_type,
        )
    )

    query_results = db.session.execute(stmt).all()

    # 2. Process the query results into a structured dictionary
    # Initialize data for all 12 months to ensure every month is displayed
    report_data = {
        month_num: {
            "month_name": calendar.month_name[month_num],
            "income": decimal.Decimal(0),
            "expense": decimal.Decimal(0),
            "net": decimal.Decimal(0),
        }
        for month_num in range(1, 13)
    }

    for month_num, trans_type, total_amount in query_results:
        if trans_type == "income":
            report_data[month_num]["income"] = total_amount
        else:  # 'expense'
            report_data[month_num]["expense"] = total_amount

    # 3. Calculate the net balance for each month and grand totals
    grand_total = {"income": 0, "expense": 0, "net": 0}
    for month_data in report_data.values():
        month_data["net"] = month_data["income"] - month_data["expense"]
        grand_total["income"] += month_data["income"]
        grand_total["expense"] += month_data["expense"]
    grand_total["net"] = grand_total["income"] - grand_total["expense"]

    return render_template(
        "yearly_report.html",
        report_data=report_data,
        year=year,
        grand_total=grand_total,
    )


@main_bp.route("/report/budgets")
@login_required
def budget_report():
    """
    Handles the Budget vs. Actual spending report page.
    """
    now_utc = datetime.now(timezone.utc)
    # Default to current month/year if not provided in the URL query
    selected_year = request.args.get("year", default=now_utc.year, type=int)
    selected_month = request.args.get("month", default=now_utc.month, type=int)

    # --- Data Fetching and Processing ---
    # 1. Get all budgets for the selected period
    budgets_stmt = select(Budget).filter_by(
        user_id=current_user.id, month=selected_month, year=selected_year
    )
    budgets_for_period = db.session.execute(budgets_stmt).scalars().all()

    # 2. Get all categorized expenses for the selected period in one query
    expenses_stmt = (
        select(transaction_categories.c.category_id, func.sum(Transaction.amount))
        .join(Transaction, Transaction.id == transaction_categories.c.transaction_id)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            func.extract("month", Transaction.transaction_date) == selected_month,
            func.extract("year", Transaction.transaction_date) == selected_year,
            Transaction.affects_balance == True,
        )
        .group_by(transaction_categories.c.category_id)
    )

    spending_by_category = {
        row[0]: row[1] for row in db.session.execute(expenses_stmt).all()
    }

    # 3. Process the data for the template
    report_data = []
    for budget in budgets_for_period:
        actual_spent = spending_by_category.get(budget.category_id, decimal.Decimal(0))
        difference = budget.amount - actual_spent

        report_data.append(
            {
                "category_name": budget.category.name,
                "budgeted_amount": budget.amount,
                "actual_spent": actual_spent,
                "difference": difference,
            }
        )

    # Data for the dropdown selectors
    years = range(now_utc.year + 1, now_utc.year - 5, -1)
    month_names = {i: name for i, name in enumerate(calendar.month_name) if i > 0}

    return render_template(
        "budget_report.html",
        report_data=report_data,
        years=years,
        month_names=month_names,
        selected_year=selected_year,
        selected_month=selected_month,
    )


@main_bp.route("/report/net_worth")
@login_required
def net_worth_report():
    """
    Calculates and displays the user's total net worth by combining
    cash accounts and investment portfolio market value.
    """
    # --- 1. Calculate Total Cash from All Accounts ---
    total_cash_query = (
        db.session.query(func.sum(Account.balance))
        .filter(Account.user_id == current_user.id)
        .scalar()
    )
    total_cash = total_cash_query or decimal.Decimal("0.0")

    # Get a list of all accounts for the breakdown table
    accounts_list = (
        db.session.execute(
            select(Account).filter_by(user_id=current_user.id).order_by(Account.name)
        )
        .scalars()
        .all()
    )

    # --- 2. Calculate Total Investment Value (adapted from portfolio route) ---
    holdings_query = (
        db.session.query(
            Asset.ticker_symbol,
            Asset.name,
            func.sum(
                case(
                    (
                        InvestmentTransaction.transaction_type == "buy",
                        InvestmentTransaction.quantity,
                    ),
                    (
                        InvestmentTransaction.transaction_type == "sell",
                        -InvestmentTransaction.quantity,
                    ),
                    else_=0,
                )
            ).label("total_quantity"),
        )
        .join(Asset, InvestmentTransaction.asset_id == Asset.id)
        .filter(InvestmentTransaction.user_id == current_user.id)
        .group_by(Asset.ticker_symbol, Asset.name)
        .all()
    )

    investment_details = []
    total_investment_value = decimal.Decimal("0.0")

    # Clear the API price cache for a fresh fetch
    from . import services

    if hasattr(services, "price_cache"):
        services.price_cache.clear()

    for holding in holdings_query:
        if holding.total_quantity > 0:
            current_price_float = get_stock_price(holding.ticker_symbol)
            market_value = decimal.Decimal("0.0")

            if current_price_float is not None:
                current_price_decimal = decimal.Decimal(str(current_price_float))
                market_value = holding.total_quantity * current_price_decimal
                total_investment_value += market_value

            investment_details.append(
                {
                    "ticker": holding.ticker_symbol,
                    "name": holding.name,
                    "quantity": holding.total_quantity,
                    "market_value": market_value,
                }
            )

    # --- 3. Calculate Final Net Worth ---
    total_net_worth = total_cash + total_investment_value

    return render_template(
        "net_worth_report.html",
        total_cash=total_cash,
        total_investments=total_investment_value,
        total_net_worth=total_net_worth,
        accounts=accounts_list,
        investments=investment_details,
    )


@main_bp.route("/report/category_trend")
@login_required
def category_trend_report():
    """
    Renders the page for the category spending trend report.
    Passes data needed to populate the selection form.
    """
    # Get the selected category and year from the URL query parameters
    selected_category_id = request.args.get("category_id", type=int)
    selected_year = request.args.get(
        "year", default=datetime.now(timezone.utc).year, type=int
    )

    # Fetch all of the user's categories to populate the dropdown
    user_categories = (
        db.session.execute(
            select(Category).filter_by(user_id=current_user.id).order_by(Category.name)
        )
        .scalars()
        .all()
    )

    # Create a list of years for the year dropdown
    current_year = datetime.now(timezone.utc).year
    years_for_dropdown = range(current_year, current_year - 5, -1)

    return render_template(
        "category_trend.html",
        categories=user_categories,
        years=years_for_dropdown,
        selected_category_id=selected_category_id,
        selected_year=selected_year,
    )


@main_bp.route("/api/monthly_spending")
@login_required
def monthly_spending_api():
    """
    API endpoint that returns the total monthly spending for a given
    category and year, formatted for a bar chart.
    """
    category_id = request.args.get("category_id", type=int)
    year = request.args.get("year", type=int)

    if not category_id or not year:
        return jsonify({"error": "A category_id and year are required."}), 400

    # --- THIS IS THE CORRECTED QUERY ---
    spending_data = (
        db.session.query(
            func.extract("month", Transaction.transaction_date).label("month"),
            func.sum(Transaction.amount).label("total"),
        )
        .join(transaction_categories)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            Transaction.affects_balance == True,
            transaction_categories.c.category_id == category_id,
            func.extract("year", Transaction.transaction_date) == year,
        )
        .group_by(
            # The fix is here: We group by the function call itself, not the alias 'month'.
            func.extract("month", Transaction.transaction_date)
        )
        .all()
    )
    # --- END OF CORRECTED QUERY ---

    # Initialize a list of 12 zeros, one for each month
    monthly_totals = [0] * 12
    for row in spending_data:
        month_index = int(row.month) - 1
        monthly_totals[month_index] = float(row.total)

    chart_data = {
        "labels": [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        "data": monthly_totals,
    }

    return jsonify(chart_data)


@main_bp.route("/export-transactions")
@login_required
def export_transactions():
    """
    Generates a CSV file of transactions. Exports ALL transactions by default,
    or a filtered set if filter parameters are provided in the URL.
    """
    try:
        # --- THIS IS THE FIX: The full filtering logic is now included ---
        search_query = request.args.get("q", "").strip()
        trans_type = request.args.get("type", "").strip()
        account_id = request.args.get("account_id", type=int)
        category_id = request.args.get("category_id", type=int)
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        stmt = (
            db.select(Transaction)
            .options(
                selectinload(Transaction.account),
                selectinload(Transaction.categories),
                selectinload(Transaction.tags),
            )
            .filter_by(user_id=current_user.id)
        )

        # Apply all filters exactly like the main transactions page
        if trans_type:
            stmt = stmt.where(Transaction.transaction_type == trans_type)
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)
        if category_id:
            stmt = stmt.where(Transaction.categories.any(id=category_id))
        if search_query:
            search_term = f"%{search_query}%"
            stmt = (
                stmt.join(Transaction.categories, isouter=True)
                .join(Transaction.tags, isouter=True)
                .filter(
                    or_(
                        Transaction.description.ilike(search_term),
                        Transaction.notes.ilike(search_term),
                        Category.name.ilike(search_term),
                        Tag.name.ilike(search_term),
                    )
                )
                .distinct()
            )
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date_inclusive = datetime.combine(
                datetime.strptime(end_date_str, "%Y-%m-%d").date(), datetime.max.time()
            )
            stmt = stmt.where(
                Transaction.transaction_date.between(start_date, end_date_inclusive)
            )
        # --- END OF FIX ---

        # Execute the (now filtered) query to get all matching results
        stmt = stmt.order_by(Transaction.transaction_date.desc())
        transactions_to_export = db.session.execute(stmt).scalars().all()

        # Generate the CSV file in memory
        string_io = io.StringIO()
        csv_writer = csv.writer(string_io)
        csv_writer.writerow(
            [
                "Date",
                "Time",
                "Description",
                "Amount",
                "DR/CR",
                "Account",
                "Is Expense?",
                "Categories",
                "Tags",
                "Notes",
            ]
        )

        for t in transactions_to_export:
            category_names = ";".join(sorted([c.name for c in t.categories]))
            tag_names = ";".join(sorted([tag.name for tag in t.tags]))
            dr_cr = "DR" if t.transaction_type == "expense" else "CR"
            is_expense = ""
            if t.transaction_type == "expense":
                is_expense = "Yes" if t.affects_balance else "No"
            csv_writer.writerow(
                [
                    t.transaction_date.strftime("%Y-%m-%d"),
                    t.transaction_date.strftime("%I:%M %p"),
                    t.description,
                    t.amount,
                    dr_cr,
                    f"{t.account.name} ({t.account.account_type})" if t.account else "",
                    is_expense,
                    category_names,
                    tag_names,
                    t.notes or "",
                ]
            )

        output = string_io.getvalue()
        filename = f"transactions_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        current_app.logger.error(f"Failed to export transactions: {e}")
        flash("An error occurred while generating the export file.", "danger")
        return redirect(url_for("main.transactions"))


@main_bp.route("/api/transaction-summary")
@login_required
def transaction_summary_api():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if not start_date_str or not end_date_str:
        return jsonify({"labels": [], "data": []})  # Return empty if no dates

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    end_date_inclusive = datetime.combine(end_date, datetime.max.time())

    stmt = (
        select(Category.name, func.sum(Transaction.amount))
        .join(
            transaction_categories, Category.id == transaction_categories.c.category_id
        )
        .join(Transaction, Transaction.id == transaction_categories.c.transaction_id)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date.between(start_date, end_date_inclusive),
            Transaction.affects_balance == True,
        )
        .group_by(Category.name)
    )

    summary = db.session.execute(stmt).all()

    return jsonify(
        {
            "labels": [row[0] for row in summary],
            "data": [float(row[1]) for row in summary],
        }
    )


@main_bp.route("/api/daily_expense_trend")
@login_required
def daily_expense_trend():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if not start_date_str or not end_date_str:
        return jsonify({"labels": [], "data": []})  # Return empty if no dates

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    end_date_inclusive = datetime.combine(end_date, datetime.max.time())

    stmt = (
        select(
            func.cast(Transaction.transaction_date, db.Date).label("date"),
            func.sum(Transaction.amount).label("total_expenses"),
        )
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date.between(start_date, end_date_inclusive),
            Transaction.affects_balance == True,
        )
        .group_by(func.cast(Transaction.transaction_date, db.Date))
        .order_by(func.cast(Transaction.transaction_date, db.Date))
    )
    daily_expenses_query = db.session.execute(stmt).all()

    # Build a complete date range to ensure all days are represented
    date_range = (
        start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)
    )
    trend_data = {dt.strftime("%Y-%m-%d"): 0 for dt in date_range}

    for day in daily_expenses_query:
        trend_data[day.date.strftime("%Y-%m-%d")] = float(day.total_expenses)

    return jsonify(
        {"labels": list(trend_data.keys()), "data": list(trend_data.values())}
    )


@main_bp.route("/api/check-username")
def check_username():
    """Checks if a username is already taken."""
    username = request.args.get("username", "").strip()

    # Don't check for empty or very short usernames
    if len(username) < 3:
        # Return a neutral or empty response
        return jsonify({})

    # Query the database for an existing user with that username
    stmt = select(User).where(User.username == username)
    user = db.session.execute(stmt).scalar_one_or_none()

    # Return a JSON response indicating if the username is available
    if user:
        return jsonify({"available": False})
    else:
        return jsonify({"available": True})


@main_bp.route("/api/check-email")
def check_email():
    """Checks if an email is already taken."""
    email = request.args.get("email", "").strip().lower()

    # A simple check to see if it looks like an email
    if "@" not in email or "." not in email or len(email) < 5:
        return jsonify({})

    stmt = select(User).where(User.email == email)
    user = db.session.execute(stmt).scalar_one_or_none()

    if user:
        return jsonify({"available": False})
    else:
        return jsonify({"available": True})


@main_bp.route("/api/financial_trend")
@login_required
def financial_trend():
    """
    Provides data for a line chart comparing total daily income vs. expenses
    over a specified date range.
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if not start_date_str or not end_date_str:
        return jsonify({"error": "start_date and end_date are required"}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        end_date_inclusive = datetime.combine(end_date, datetime.max.time())
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # A single, efficient query to get daily totals for both types
    daily_totals_query = (
        db.session.query(
            db.func.cast(Transaction.transaction_date, db.Date),
            Transaction.transaction_type,
            db.func.sum(Transaction.amount),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date.between(start_date, end_date_inclusive),
            Transaction.affects_balance == True,
        )
        .group_by(
            db.func.cast(Transaction.transaction_date, db.Date),
            Transaction.transaction_type,
        )
        .order_by(db.func.cast(Transaction.transaction_date, db.Date))
        .all()
    )

    # Initialize dictionaries with all dates in the range set to zero
    date_range = [
        start_date + timedelta(days=d) for d in range((end_date - start_date).days + 1)
    ]
    income_data = {dt.strftime("%Y-%m-%d"): 0 for dt in date_range}
    expense_data = {dt.strftime("%Y-%m-%d"): 0 for dt in date_range}

    # Populate the dictionaries with data from the query
    for date, trans_type, total in daily_totals_query:
        date_str = date.strftime("%Y-%m-%d")
        if trans_type == "income":
            income_data[date_str] = float(total)
        elif trans_type == "expense":
            expense_data[date_str] = float(total)

    response_data = {
        "labels": list(income_data.keys()),
        "income_data": list(income_data.values()),
        "expense_data": list(expense_data.values()),
    }

    return jsonify(response_data)


@main_bp.route("/recurring", methods=["GET", "POST"])
@login_required
def recurring_transactions():
    if request.method == "POST":
        start_date_str = request.form.get("start_date")
        if not start_date_str:
            flash("Start date is required.", "error")
            return redirect(url_for("main.recurring_transactions"))

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

        new_recurring = RecurringTransaction(
            user_id=current_user.id,
            description=request.form.get("description"),
            amount=decimal.Decimal(request.form.get("amount")),
            transaction_type=request.form.get("transaction_type"),
            recurrence_interval=request.form.get("recurrence_interval"),
            start_date=start_date,
            next_due_date=start_date,
            account_id=int(request.form.get("account_id")),
            category_id=(
                int(request.form.get("category_id"))
                if request.form.get("category_id")
                else None
            ),
        )
        db.session.add(new_recurring)
        db.session.commit()
        flash("Recurring transaction scheduled successfully!", "success")
        return redirect(url_for("main.recurring_transactions"))

    # --- Logic for GET request ---
    accounts = (
        db.session.execute(select(Account).filter_by(user_id=current_user.id))
        .scalars()
        .all()
    )
    categories = (
        db.session.execute(
            select(Category).filter_by(user_id=current_user.id).order_by(Category.name)
        )
        .scalars()
        .all()
    )
    recurring_list = (
        db.session.execute(
            select(RecurringTransaction)
            .filter_by(user_id=current_user.id)
            .order_by(RecurringTransaction.next_due_date)
        )
        .scalars()
        .all()
    )

    return render_template(
        "recurring.html",
        accounts=accounts,
        categories=categories,
        recurring_list=recurring_list,
    )


@main_bp.route("/tasks/generate_recurring", methods=["POST"])
def generate_recurring_transactions():
    """
    A protected task endpoint to generate transactions from recurring rules.
    This should only be triggered by a secured, scheduled job.
    """
    # 1. Security Check: Verify the secret key from the request header
    task_secret_key = current_app.config.get("TASK_SECRET_KEY")
    request_secret = request.headers.get("X-App-Key")

    # Abort if secrets are missing or do not match
    if not task_secret_key or request_secret != task_secret_key:
        current_app.logger.warning(
            "Unauthorized attempt to access recurring task endpoint."
        )
        abort(403)  # Use abort(403) for "Forbidden"

    # 2. Get today's date
    today = datetime.now(timezone.utc).date()
    current_app.logger.info(f"Running recurring transaction job on {today}...")

    # 3. Find all due recurring rules
    due_rules_stmt = select(RecurringTransaction).where(
        RecurringTransaction.next_due_date <= today
    )
    due_rules = db.session.execute(due_rules_stmt).scalars().all()

    if not due_rules:
        current_app.logger.info("No recurring transactions are due today.")
        return jsonify({"status": "success", "message": "No transactions to generate."})

    transactions_created = 0
    for rule in due_rules:
        transaction_datetime = datetime.combine(
            rule.next_due_date, datetime.min.time(), tzinfo=timezone.utc
        )
        new_transaction = Transaction(
            description=rule.description,
            amount=rule.amount,
            transaction_type=rule.transaction_type,
            transaction_date=transaction_datetime,
            user_id=rule.user_id,
            account_id=rule.account_id,
            recurring_transaction_id=rule.id,
        )
        if rule.category:
            new_transaction.categories.append(rule.category)

        # 5. Update account balance
        if rule.account:
            if new_transaction.transaction_type == "income":
                rule.account.balance += new_transaction.amount
            else:
                rule.account.balance -= new_transaction.amount

        # 6. Calculate the next due date
        if rule.recurrence_interval == "daily":
            rule.next_due_date += timedelta(days=1)
        elif rule.recurrence_interval == "weekly":
            rule.next_due_date += timedelta(weeks=1)
        elif rule.recurrence_interval == "monthly":
            rule.next_due_date += relativedelta(months=1)
        elif rule.recurrence_interval == "yearly":
            rule.next_due_date += relativedelta(years=1)

        db.session.add(new_transaction)
        transactions_created += 1

    # 7. Commit all changes to the database
    db.session.commit()

    success_message = f"Successfully generated {transactions_created} transaction(s)."
    current_app.logger.info(success_message)
    return jsonify({"status": "success", "message": success_message})


@main_bp.route("/recurring/<int:recurring_id>/transactions")
@login_required
def view_generated_transactions(recurring_id):
    """Displays all transactions generated by a specific recurring rule."""

    # Find the parent recurring rule, ensuring it belongs to the current user
    rule = db.session.get(RecurringTransaction, recurring_id)
    if not rule or rule.user_id != current_user.id:
        abort(404)

    # The 'generated_transactions' relationship we created makes this query simple.
    # We order them by date for a clean display.
    transactions = rule.generated_transactions.order_by(
        Transaction.transaction_date.desc()
    ).all()

    return render_template(
        "recurring_detail.html", rule=rule, transactions=transactions
    )


@main_bp.route("/recurring/edit/<int:recurring_id>", methods=["GET", "POST"])
@login_required
def edit_recurring(recurring_id):
    rule = db.get_or_404(RecurringTransaction, recurring_id)
    if rule.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        # Update the rule with form data
        rule.description = request.form.get("description")
        rule.amount = decimal.Decimal(request.form.get("amount"))
        rule.transaction_type = request.form.get("transaction_type")
        rule.recurrence_interval = request.form.get("recurrence_interval")
        rule.start_date = datetime.strptime(
            request.form.get("start_date"), "%Y-%m-%d"
        ).date()
        rule.account_id = int(request.form.get("account_id"))
        rule.category_id = (
            int(request.form.get("category_id"))
            if request.form.get("category_id")
            else None
        )

        db.session.commit()
        flash("Recurring transaction rule updated successfully!", "success")
        return redirect(url_for("main.recurring_transactions"))

    # For a GET request, fetch data needed for the form dropdowns
    accounts = (
        db.session.execute(select(Account).filter_by(user_id=current_user.id))
        .scalars()
        .all()
    )
    categories = (
        db.session.execute(
            select(Category).filter_by(user_id=current_user.id).order_by(Category.name)
        )
        .scalars()
        .all()
    )
    return render_template(
        "edit_recurring.html", rule=rule, accounts=accounts, categories=categories
    )


@main_bp.route("/recurring/delete/<int:recurring_id>", methods=["POST"])
@login_required
def delete_recurring(recurring_id):
    rule = db.get_or_404(RecurringTransaction, recurring_id)
    if rule.user_id != current_user.id:
        abort(403)

    # The 'cascade' option on the model will handle generated transactions if set up,
    # otherwise, we simply delete the rule itself.
    db.session.delete(rule)
    db.session.commit()
    flash("Recurring transaction rule deleted successfully.", "success")
    return redirect(url_for("main.recurring_transactions"))


@main_bp.route("/recurring/run/<int:recurring_id>", methods=["POST"])
@login_required
def run_recurring_now(recurring_id):
    rule = db.get_or_404(RecurringTransaction, recurring_id)
    if rule.user_id != current_user.id:
        abort(403)

    try:
        # 1. Create the new Transaction record
        now_utc = datetime.now(timezone.utc)
        new_transaction = Transaction(
            description=f"{rule.description} (Manual Run)",
            amount=rule.amount,
            transaction_type=rule.transaction_type,
            transaction_date=now_utc,
            user_id=rule.user_id,
            account_id=rule.account_id,
            recurring_transaction_id=rule.id,
        )
        if rule.category:
            new_transaction.categories.append(rule.category)

        # 2. Update the account balance
        if rule.account:
            if new_transaction.transaction_type == "income":
                rule.account.balance += new_transaction.amount
            else:
                rule.account.balance -= new_transaction.amount

        # 3. Update the rule's last processed date
        rule.last_processed_date = now_utc.date()

        db.session.add(new_transaction)
        log_activity(f"Manually ran recurring transaction: '{rule.description}'")
        db.session.commit()

        flash("Recurring transaction generated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Manual recurring run failed for rule {rule.id}: {e}")
        flash("An error occurred while generating the transaction.", "danger")

    return redirect(url_for("main.recurring_transactions"))


@main_bp.route("/portfolio/add", methods=["GET", "POST"])
@login_required
def add_investment():
    if request.method == "POST":
        datetime_str = request.form.get("transaction_date")
        ticker = request.form.get("ticker_symbol", "").strip().upper()
        trans_type = request.form.get("transaction_type")
        quantity_str = request.form.get("quantity")
        price_str = request.form.get("price_per_unit")
        date_str = request.form.get("transaction_date")

        # --- Validation (can be enhanced further) ---
        if not all([ticker, trans_type, quantity_str, price_str, date_str]):
            flash("All fields are required.", "error")
            return redirect(url_for("main.add_investment"))

        # --- "Find or Create" Asset Logic ---
        # First, try to find an existing asset with the given ticker
        asset_stmt = select(Asset).where(func.upper(Asset.ticker_symbol) == ticker)
        asset = db.session.execute(asset_stmt).scalar_one_or_none()

        # If the asset doesn't exist, create a new one
        if not asset:
            # For now, we'll use the ticker as the name and default the type
            asset = Asset(
                name=ticker,  # In a real app, you might fetch this from an API
                ticker_symbol=ticker,
                asset_type="Stock",  # Default asset type
            )
            db.session.add(asset)
            # We don't commit yet; it will be part of the transaction's commit
            flash(f"New asset {ticker} added to your database.", "info")

        # --- Create the InvestmentTransaction ---
        new_investment_trans = InvestmentTransaction(
            user_id=current_user.id,
            asset=asset,  # Link to the found or newly created asset
            transaction_type=trans_type,
            quantity=decimal.Decimal(quantity_str),
            price_per_unit=decimal.Decimal(price_str),
            transaction_date=datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M"),
        )

        db.session.add(new_investment_trans)
        db.session.commit()

        flash("Investment transaction recorded successfully!", "success")
        return redirect(url_for("main.portfolio"))

    # For a GET request, just show the form
    return render_template("add_investment.html")


# In finance_tracker/routes.py


@main_bp.route("/portfolio/edit/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def edit_investment_transaction(transaction_id):
    trans = db.get_or_404(InvestmentTransaction, transaction_id)
    if trans.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        # --- 1. Handle Ticker Symbol Change (Find or Create Asset) ---
        new_ticker = request.form.get("ticker_symbol", "").strip().upper()
        if new_ticker:
            asset = db.session.execute(
                select(Asset).filter_by(ticker_symbol=new_ticker)
            ).scalar_one_or_none()

            if not asset:
                asset = Asset(
                    ticker_symbol=new_ticker, name=new_ticker, asset_type="Stock"
                )
                db.session.add(asset)

            trans.asset = asset

        # --- 2. Update Transaction Details from Form ---
        trans.transaction_type = request.form.get("transaction_type")
        trans.quantity = decimal.Decimal(request.form.get("quantity"))
        trans.price_per_unit = decimal.Decimal(request.form.get("price_per_unit"))

        # --- THIS IS THE FIX ---
        # Get the datetime string from the form and parse it with the correct format.
        datetime_str = request.form.get("transaction_date")
        if datetime_str:
            trans.transaction_date = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
        # --- END OF FIX ---

        log_activity(f"Updated investment transaction for {trans.asset.ticker_symbol}.")
        db.session.commit()
        flash("Investment transaction updated successfully!", "success")
        return redirect(url_for("main.portfolio"))

    # For a GET request, simply render the template with the transaction object.
    # The template itself handles formatting the date for the input field.
    return render_template("edit_investment.html", trans=trans)


@main_bp.route("/portfolio/delete/<int:transaction_id>", methods=["POST"])
@login_required
def delete_investment_transaction(transaction_id):
    trans = db.get_or_404(InvestmentTransaction, transaction_id)

    # --- ADD THE SAME SECURITY CHECK HERE ---
    if trans.user_id != current_user.id:
        abort(403)
    # --- END OF CHECK ---

    log_activity(
        f"Deleted {trans.transaction_type} of {trans.quantity} {trans.asset.ticker_symbol} from portfolio."
    )
    db.session.delete(trans)
    db.session.commit()
    flash("Investment transaction deleted.", "success")
    return redirect(url_for("main.portfolio"))
