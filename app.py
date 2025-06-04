# app.py
from datetime import datetime
import os

# --- Expense Class Definition (with __str__ and __repr__) ---
class Expense:
    """
    Represents a single expense item.
    """
    EXPENSE_TYPE = "STANDARD" # Class attribute to identify type

    def __init__(self, description, amount, category, timestamp=None):
        self.description = str(description) # Ensure description is string
        self.amount = float(amount)
        self.category = str(category) # Ensure category is string
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now().isoformat()

    def to_file_string(self):
        """
        Returns a comma-separated string representation for file storage, prefixed by type.
        """
        return f"{self.EXPENSE_TYPE},{self.description},{str(self.amount)},{self.category},{self.timestamp}\n"

    def display(self, index):
        """
        Prints the details of this expense object in a formatted row.
        """
        desc_display = (self.description[:22] + '...') if len(self.description) > 25 else self.description
        cat_display = (self.category[:17] + '...') if len(self.category) > 20 else self.category
        display_timestamp = self.timestamp[:19].replace("T", " ")

        # For standard expense, recurrence column will be empty
        print(f"{index:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{self.amount:<10.2f} | {cat_display:<20} | {'N/A':<15}")

    def __str__(self):
        """
        User-friendly string representation of the expense.
        """
        return f"Expense: {self.description} ({self.category}) - ₹{self.amount:.2f} on {self.timestamp[:10]}"

    def __repr__(self):
        """
        Official string representation of the expense, ideally evaluatable.
        """
        return f"Expense(description='{self.description}', amount={self.amount}, category='{self.category}', timestamp='{self.timestamp}')"

# --- RecurringExpense Class Definition (inherits from Expense) ---
class RecurringExpense(Expense):
    """
    Represents a recurring expense item, inheriting from Expense.
    """
    EXPENSE_TYPE = "RECURRING" # Class attribute to identify type

    def __init__(self, description, amount, category, recurrence_period, timestamp=None):
        super().__init__(description, amount, category, timestamp) # Call parent's __init__
        self.recurrence_period = str(recurrence_period) # e.g., "Monthly", "Yearly"

    def to_file_string(self):
        """
        Returns a comma-separated string representation including recurrence period, prefixed by type.
        """
        # Get base string from parent, remove newline, add recurrence, add newline
        # Or, more simply, construct it fully here ensuring type is correct.
        return f"{self.EXPENSE_TYPE},{self.description},{str(self.amount)},{self.category},{self.timestamp},{self.recurrence_period}\n"

    def display(self, index):
        """
        Prints the details of this recurring expense, including recurrence period.
        """
        desc_display = (self.description[:22] + '...') if len(self.description) > 25 else self.description
        cat_display = (self.category[:17] + '...') if len(self.category) > 20 else self.category
        display_timestamp = self.timestamp[:19].replace("T", " ")
        period_display = (self.recurrence_period[:12] + '...') if len(self.recurrence_period) > 15 else self.recurrence_period

        print(f"{index:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{self.amount:<10.2f} | {cat_display:<20} | {period_display:<15}")

    def __str__(self):
        """
        User-friendly string representation for RecurringExpense.
        """
        return f"Recurring Expense: {self.description} ({self.category}) - ₹{self.amount:.2f} ({self.recurrence_period}) on {self.timestamp[:10]}"

    def __repr__(self):
        """
        Official string representation for RecurringExpense.
        """
        return f"RecurringExpense(description='{self.description}', amount={self.amount}, category='{self.category}', recurrence_period='{self.recurrence_period}', timestamp='{self.timestamp}')"


# --- File Handling Functions (Updated for different Expense types) ---

def save_expenses_to_file(all_expenses_list, filename="expenses.txt"):
    """ Saves the list of Expense objects (standard or recurring) to a file. """
    try:
        with open(filename, "w") as f:
            for expense_obj in all_expenses_list:
                f.write(expense_obj.to_file_string())
        print(f"Expenses successfully saved to {filename}")
    except IOError:
        print(f"Error: Could not save expenses to {filename}.")

def load_expenses_from_file(filename="expenses.txt"):
    """ Loads expenses from a file, creating Expense or RecurringExpense objects. """
    loaded_expenses_objects = []
    try:
        with open(filename, "r") as f:
            for line_number, line in enumerate(f, 1):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                
                parts = stripped_line.split(',')
                expense_type = parts[0]

                try:
                    if expense_type == Expense.EXPENSE_TYPE and len(parts) == 5:
                        # STANDARD,description,amount,category,timestamp
                        description, amount_str, category, timestamp_str = parts[1], parts[2], parts[3], parts[4]
                        expense_obj = Expense(description, float(amount_str), category, timestamp_str)
                        loaded_expenses_objects.append(expense_obj)
                    elif expense_type == RecurringExpense.EXPENSE_TYPE and len(parts) == 6:
                        # RECURRING,description,amount,category,timestamp,recurrence_period
                        description, amount_str, category, timestamp_str, recurrence_period = parts[1], parts[2], parts[3], parts[4], parts[5]
                        expense_obj = RecurringExpense(description, float(amount_str), category, recurrence_period, timestamp_str)
                        loaded_expenses_objects.append(expense_obj)
                    else:
                        print(f"Warning: Skipping malformed line #{line_number} in {filename}: Unknown type or incorrect parts. Line: '{line.strip()}'")
                except ValueError:
                    print(f"Warning: Skipping corrupted data on line #{line_number} in {filename} (amount not a number): '{line.strip()}'")
                except IndexError:
                    print(f"Warning: Skipping malformed line #{line_number} in {filename} (not enough parts for type '{expense_type}'): '{line.strip()}'")
            
            if loaded_expenses_objects:
                 print(f"Successfully loaded {len(loaded_expenses_objects)} expenses from {filename}")
            else:
                print(f"No valid expense data found in {filename} or file was empty.")

    except FileNotFoundError:
        print(f"No previous expenses file found at '{filename}'. Starting fresh.")
    except IOError:
        print(f"Error: Could not read expenses from {filename}.")
    return loaded_expenses_objects

# --- Core Expense Logic Functions (largely unchanged, operate on Expense objects) ---

expenses = [] 

def log_standard_expense_details(): # Renamed to be specific
    """ Prompts for standard expense details, creates an Expense object, and returns it. """
    print("\n--- Log New Standard Expense ---")
    description = input("Enter expense description: ").strip()
    amount = 0.0
    while True:
        try:
            amount_str = input("Enter expense amount (in ₹): ")
            amount = float(amount_str)
            if amount <= 0:
                print("Amount must be positive.")
            else:
                break
        except ValueError:
            print("Invalid amount. Please enter a numeric value.")

    category_input = input("Enter expense category (e.g., Food, Bills) [Default: General]: ").strip().title()
    category = category_input if category_input else "General"
    
    new_expense = Expense(description, amount, category)
    print(f"Standard Expense Logged: {new_expense.description}")
    return new_expense

# For this exercise, we'll add recurring expenses manually in main,
# but a log_recurring_expense_details() function would be similar.

def record_new_expenses(num_standard_to_log):
    """Records a specified number of standard expenses."""
    global expenses
    if num_standard_to_log > 0:
        print(f"\n--- Preparing to log {num_standard_to_log} new standard expenses ---")
        for i in range(num_standard_to_log):
            print(f"\nLogging new standard expense #{i+1} of {num_standard_to_log}:")
            new_expense_obj = log_standard_expense_details()
            expenses.append(new_expense_obj)

def view_all_expenses(all_expenses_list):
    """ Prints all expenses from the provided list of Expense objects (standard or recurring). """
    print("\n--- Viewing All Expenses ---")
    if not all_expenses_list:
        print("No expenses recorded yet.")
        return

    # Updated header for recurrence period
    header = f"{'#':<3} | {'Timestamp':<26} | {'Description':<25} | {'Amount (₹)':<12} | {'Category':<20} | {'Recurrence':<15}"
    print(header)
    print("-" * len(header))
    
    for idx, expense_obj in enumerate(all_expenses_list):
        expense_obj.display(idx + 1) # Polymorphism: Calls display() of Expense or RecurringExpense
    print("-" * len(header))

def get_total_expenses(all_expenses_list):
    """ Calculates the total amount from a list of Expense objects. """
    total = 0.0
    for expense_obj in all_expenses_list:
        if isinstance(expense_obj.amount, (int, float)):
            total += expense_obj.amount
        else:
            print(f"Warning: Expense '{expense_obj.description}' has an invalid amount type.")
    return total

# --- Main Application Execution ---
if __name__ == "__main__":
    expenses_file = "expenses_oop.txt" # New filename for this version
    expenses = load_expenses_from_file(expenses_file)

    print(f"\nWelcome to your Personal Finance Tracker CLI (OOP Version)!")
    print(f"Current System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Loaded {len(expenses)} expenses from '{expenses_file}'.")

    # Demonstrate __str__ and __repr__ if some expenses were loaded
    if expenses:
        print("\n--- Demonstrating __str__ and __repr__ for the first loaded expense (if any) ---")
        print(f"Using print(expense_obj) (calls __str__): {expenses[0]}")
        print(f"Using repr(expense_obj) (calls __repr__): {repr(expenses[0])}")

    num_std_expenses_to_log = 0
    try:
        num_std_expenses_to_log = int(input("\nHow many new standard expenses would you like to log? (e.g., 1, 0 to skip): "))
        if num_std_expenses_to_log < 0: num_std_expenses_to_log = 0
    except ValueError:
        print("Invalid number, skipping new standard expense logging.")

    if num_std_expenses_to_log > 0:
        record_new_expenses(num_std_expenses_to_log)
    
    # Manually add a Recurring Expense for demonstration
    add_recurring = input("Add a sample recurring expense? (yes/no): ").strip().lower()
    if add_recurring == 'yes':
        print("Adding a sample recurring expense...")
        netflix_subscription = RecurringExpense("Netflix Subscription", 649.00, "Entertainment", "Monthly")
        amazon_prime = RecurringExpense("Amazon Prime", 1499.00, "Subscription", "Yearly")
        expenses.append(netflix_subscription)
        expenses.append(amazon_prime)
        print(f"Added: {netflix_subscription.description}")
        print(f"Added: {amazon_prime.description}")

        print("\n--- Demonstrating __str__ and __repr__ for a recurring expense ---")
        print(f"Using print(netflix_subscription) (calls __str__): {netflix_subscription}")
        print(f"Using repr(netflix_subscription) (calls __repr__): {repr(netflix_subscription)}")


    if expenses:
        view_all_expenses(expenses)
        total_spent = get_total_expenses(expenses)
        print(f"\n--- Total Expenses ---")
        print(f"You have spent a total of: ₹{total_spent:.2f}")
    else:
        print("\nNo expenses recorded to display or total.")

    if expenses:
        save_expenses_to_file(expenses, expenses_file)
    else:
        print("No expenses to save.")
        
    print("\nExiting application.")