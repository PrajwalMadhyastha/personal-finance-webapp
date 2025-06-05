# finance_tracker/models.py
from datetime import datetime # Ensure datetime is imported here

# --- Expense Class Definition (remains the same) ---
class Expense:
    EXPENSE_TYPE = "STANDARD"
    def __init__(self, description, amount, category, timestamp=None):
        self.description = str(description)
        self.amount = float(amount)
        self.category = str(category)
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now().isoformat()

    def to_file_string(self):
        return f"{self.EXPENSE_TYPE},{self.description},{str(self.amount)},{self.category},{self.timestamp}\n"

    def display(self, index):
        desc_display = (self.description[:22] + '...') if len(self.description) > 25 else self.description
        cat_display = (self.category[:17] + '...') if len(self.category) > 20 else self.category
        display_timestamp = self.timestamp[:19].replace("T", " ")
        print(f"{index:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{self.amount:<10.2f} | {cat_display:<20} | {'N/A':<15}")

    def __str__(self):
        return f"Expense: {self.description} ({self.category}) - ₹{self.amount:.2f} on {self.timestamp[:10]}"

    def __repr__(self):
        return f"Expense(description='{self.description}', amount={self.amount}, category='{self.category}', timestamp='{self.timestamp}')"

# --- RecurringExpense Class Definition (remains the same) ---
class RecurringExpense(Expense):
    EXPENSE_TYPE = "RECURRING"
    def __init__(self, description, amount, category, recurrence_period, timestamp=None):
        super().__init__(description, amount, category, timestamp)
        self.recurrence_period = str(recurrence_period)

    def to_file_string(self):
        return f"{self.EXPENSE_TYPE},{self.description},{str(self.amount)},{self.category},{self.timestamp},{self.recurrence_period}\n"

    def display(self, index):
        desc_display = (self.description[:22] + '...') if len(self.description) > 25 else self.description
        cat_display = (self.category[:17] + '...') if len(self.category) > 20 else self.category
        display_timestamp = self.timestamp[:19].replace("T", " ")
        period_display = (self.recurrence_period[:12] + '...') if len(self.recurrence_period) > 15 else self.recurrence_period
        print(f"{index:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{self.amount:<10.2f} | {cat_display:<20} | {period_display:<15}")

    def __str__(self):
        return f"Recurring Expense: {self.description} ({self.category}) - ₹{self.amount:.2f} ({self.recurrence_period}) on {self.timestamp[:10]}"

    def __repr__(self):
        return f"RecurringExpense(description='{self.description}', amount={self.amount}, category='{self.category}', recurrence_period='{self.recurrence_period}', timestamp='{self.timestamp}')"

# --- Updated User Class ---
class User:
    """
    Represents a user of the finance application, managing their own expenses.
    """
    def __init__(self, username, email=None, user_id=None):
        # Assign attributes that _generate_simple_id might depend on FIRST
        self.username = str(username) # Ensure username is a string
        self.email = str(email) if email is not None else None # Ensure email is string or None

        # Now self.username is set and can be safely used by _generate_simple_id
        self.user_id = user_id if user_id else self._generate_simple_id()
        
        self.expenses = [] # Each user now has their own list of expense objects

    def _generate_simple_id(self):
        # Simple pseudo-ID for now, replace with something robust later (e.g., UUID)
        # This method now safely uses self.username
        return str(abs(hash(self.username + datetime.now().isoformat())))[:8]

    def add_expense(self, expense_object):
        # (Make sure Expense and RecurringExpense are defined above this class or imported)
        if isinstance(expense_object, (Expense, RecurringExpense)): # Type check
            self.expenses.append(expense_object)
            print(f"Expense '{expense_object.description}' added to user {self.username}.")
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
        total = 0.0
        for expense_obj in self.expenses:
            if isinstance(expense_obj.amount, (int, float)):
                total += expense_obj.amount
        return total

    def __str__(self):
        email_str = f", Email: {self.email}" if self.email else ""
        return f"User(ID: {self.user_id}, Username: {self.username}{email_str}, Expenses: {len(self.expenses)})"

    def __repr__(self):
        return f"User(user_id='{self.user_id}', username='{self.username}', email='{self.email}')"