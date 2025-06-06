# finance_tracker/models.py
from . import db
from datetime import datetime

# --- The Single, Correct Expense Model ---
class Expense(db.Model):
    # This attribute helps us identify the type when loading from a file/JSON
    EXPENSE_TYPE = "STANDARD"
    
    # --- SQLAlchemy Column Definitions ---
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # --- Methods Merged from Your Old Plain Class ---
    def to_dict(self):
        """Converts the Expense object to a dictionary for JSON serialization."""
        return {
            "expense_type": self.EXPENSE_TYPE,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "timestamp": self.timestamp.isoformat() # Convert datetime object to string for JSON
        }

    def display(self, index):
        """Prints the details of this expense object in a formatted row."""
        desc_display = (self.description[:22] + '...') if len(self.description) > 25 else self.description
        cat_display = (self.category[:17] + '...') if len(self.category) > 20 else self.category
        display_timestamp = self.timestamp.strftime('%Y-%m-%d %H:%M:%S') # Use strftime for datetime object
        print(f"{index:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{self.amount:<10.2f} | {cat_display:<20} | {'N/A':<15}")

    def __str__(self):
        """User-friendly string representation of the expense."""
        return f"Expense: {self.description} ({self.category}) - ₹{self.amount:.2f} on {self.timestamp.strftime('%Y-%m-%d')}"

    def __repr__(self):
        """Developer-friendly representation of the object."""
        return f"<Expense ID: {self.id}, Desc: {self.description}>"


# --- The RecurringExpense Model ---
# Now correctly inherits from the one true Expense(db.Model)
class RecurringExpense(Expense):
    EXPENSE_TYPE = "RECURRING"
    
    # We add a new column for the recurrence period
    __mapper_args__ = {'polymorphic_identity': 'recurring'} # SQLAlchemy-specific way to handle inheritance
    id = db.Column(db.Integer, db.ForeignKey('expense.id'), primary_key=True) # Link to parent table
    recurrence_period = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        """Converts the RecurringExpense object to a dictionary."""
        data = super().to_dict() # Gets base dict from Expense model
        data["recurrence_period"] = self.recurrence_period
        return data

    def display(self, index):
        """Prints the details of this recurring expense."""
        desc_display = (self.description[:22] + '...') if len(self.description) > 25 else self.description
        cat_display = (self.category[:17] + '...') if len(self.category) > 20 else self.category
        display_timestamp = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        period_display = (self.recurrence_period[:12] + '...') if len(self.recurrence_period) > 15 else self.recurrence_period
        print(f"{index:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{self.amount:<10.2f} | {cat_display:<20} | {period_display:<15}")

    def __str__(self):
        return f"Recurring Expense: {self.description} ({self.category}) - ₹{self.amount:.2f} ({self.recurrence_period}) on {self.timestamp.strftime('%Y-%m-%d')}"


# --- The User Model ---
# The User class definition does not need to change.
class User:
    # ... (Keep the User class exactly as it was) ...
    def __init__(self, username, email=None, user_id=None):
        self.username = str(username)
        self.email = str(email) if email is not None else None
        self.user_id = user_id if user_id else self._generate_simple_id()
        self.expenses = []

    def _generate_simple_id(self):
        return str(abs(hash(self.username + datetime.now().isoformat())))[:8]
    
    def add_expense(self, expense_object):
        if isinstance(expense_object, (Expense, RecurringExpense)):
            self.expenses.append(expense_object)
        else:
            print("Error: Invalid object type. Cannot add to expenses.")

    def view_expenses(self):
        print(f"\n--- Viewing Expenses for User: {self.username} ---")
        if not self.expenses:
            print("No expenses recorded yet for this user.")
            return
        header = f"{'#':<3} | {'Timestamp':<26} | {'Description':<25} | {'Amount (₹)':<12} | {'Category':<20} | {'Recurrence':<15}"
        print(header)
        print("-" * len(header))
        for idx, expense_obj in enumerate(self.expenses):
            expense_obj.display(idx + 1)
        print("-" * len(header))

    def get_total_expenses(self):
        valid_amounts = [expense.amount for expense in self.expenses if isinstance(expense.amount, (int, float))]
        if len(valid_amounts) < len(self.expenses):
            print("Warning: Some expenses had invalid amounts and were not included in the total.")
        return sum(valid_amounts)

    def get_expenses_by_category(self, category_name):
        target_category = category_name.strip().title()
        return [expense for expense in self.expenses if expense.category.title() == target_category]

    def __str__(self):
        email_str = f", Email: {self.email}" if self.email else ""
        return f"User(ID: {self.user_id}, Username: {self.username}{email_str}, Expenses: {len(self.expenses)})"

    def __repr__(self):
        return f"User(user_id='{self.user_id}', username='{self.username}', email='{self.email}')"