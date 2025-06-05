# finance_tracker/models.py
from datetime import datetime

class Expense:
    EXPENSE_TYPE = "STANDARD"

    def __init__(self, description, amount, category, timestamp=None):
        self.description = str(description)
        self.amount = float(amount)
        self.category = str(category)
        self.timestamp = timestamp if timestamp else datetime.now().isoformat()

    def to_file_string(self): # This will be replaced by JSON, but kept for reference if needed elsewhere
        return f"{self.EXPENSE_TYPE},{self.description},{str(self.amount)},{self.category},{self.timestamp}\n"

    def to_dict(self):
        """Converts the Expense object to a dictionary for JSON serialization."""
        return {
            "expense_type": self.EXPENSE_TYPE, # Important for distinguishing types when loading
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "timestamp": self.timestamp
        }

    def display(self, index):
        desc_display = (self.description[:22] + '...') if len(self.description) > 25 else self.description
        cat_display = (self.category[:17] + '...') if len(self.category) > 20 else self.category
        display_timestamp = self.timestamp[:19].replace("T", " ")
        print(f"{index:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{self.amount:<10.2f} | {cat_display:<20} | {'N/A':<15}")

    def __str__(self):
        return f"Expense: {self.description} ({self.category}) - ₹{self.amount:.2f} on {self.timestamp[:10]}"

    def __repr__(self):
        return f"Expense(description='{self.description}', amount={self.amount}, category='{self.category}', timestamp='{self.timestamp}')"

class RecurringExpense(Expense):
    EXPENSE_TYPE = "RECURRING"

    def __init__(self, description, amount, category, recurrence_period, timestamp=None):
        super().__init__(description, amount, category, timestamp)
        self.recurrence_period = str(recurrence_period)

    def to_file_string(self): # This will be replaced by JSON
        return f"{self.EXPENSE_TYPE},{self.description},{str(self.amount)},{self.category},{self.timestamp},{self.recurrence_period}\n"

    def to_dict(self):
        """Converts the RecurringExpense object to a dictionary, including recurrence period."""
        data = super().to_dict() # Get base dictionary from parent
        data["recurrence_period"] = self.recurrence_period
        # expense_type is already set by super().to_dict() if we ensure parent's EXPENSE_TYPE is used correctly
        # or we can explicitly set it if super() doesn't guarantee the specific subtype's EXPENSE_TYPE.
        # For clarity, let's ensure it's this class's type:
        data["expense_type"] = self.EXPENSE_TYPE 
        return data

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

class User:
    def __init__(self, username, email=None, user_id=None):
        # CORRECTED ORDER: Assign username and email BEFORE user_id might use them
        self.username = str(username)
        self.email = str(email) if email is not None else None

        # Now self.username is set and can be safely used by _generate_simple_id
        self.user_id = user_id if user_id else self._generate_simple_id()
        
        self.expenses = []

    def _generate_simple_id(self):
        # This method now safely uses self.username
        return str(abs(hash(self.username + datetime.now().isoformat())))[:8]

    def add_expense(self, expense_object):
        if isinstance(expense_object, (Expense, RecurringExpense)):
            self.expenses.append(expense_object)
            # print(f"Expense '{expense_object.description}' added to user {self.username}.") # Optional: reduce verbosity
        else:
            print("Error: Invalid object type. Cannot add to expenses.")

    def view_expenses(self):
        # (view_expenses method remains the same as previous version)
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
        """Calculates total expenses using a list comprehension to extract amounts."""
        # List comprehension practice:
        valid_amounts = [
            expense.amount 
            for expense in self.expenses 
            if isinstance(expense.amount, (int, float))
        ]
        if len(valid_amounts) < len(self.expenses):
            print("Warning: Some expenses had invalid amounts and were not included in the total.")
        return sum(valid_amounts)

    def get_expenses_by_category(self, category_name):
        """Returns a list of expenses matching a specific category, using list comprehension."""
        # Ensure category_name is compared in a consistent case, e.g., title case
        target_category = category_name.strip().title()
        return [
            expense 
            for expense in self.expenses 
            if expense.category.title() == target_category
        ]

    def __str__(self):
        email_str = f", Email: {self.email}" if self.email else ""
        return f"User(ID: {self.user_id}, Username: {self.username}{email_str}, Expenses: {len(self.expenses)})"

    def __repr__(self):
        return f"User(user_id='{self.user_id}', username='{self.username}', email='{self.email}')"