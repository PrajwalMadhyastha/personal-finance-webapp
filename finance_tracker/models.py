# finance_tracker/models.py
from . import db, bcrypt
from datetime import datetime
from flask_login import UserMixin

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
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'