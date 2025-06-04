# app.py
from datetime import datetime
import os

# --- Expense Class Definition ---
class Expense:
    """
    Represents a single expense item.
    """
    def __init__(self, description, amount, category, timestamp=None):
        """
        Initializes an Expense object.
        Args:
            description (str): Description of the expense.
            amount (float): Amount of the expense.
            category (str): Category of the expense.
            timestamp (str, optional): ISO format timestamp string. 
                                       Defaults to current time if None.
        """
        self.description = description
        self.amount = float(amount) # Ensure amount is float
        self.category = category
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now().isoformat()

    def to_file_string(self):
        """
        Returns a comma-separated string representation of the expense for file storage.
        """
        return f"{self.description},{str(self.amount)},{self.category},{self.timestamp}\n"

    def display(self, index):
        """
        Prints the details of this expense object in a formatted row.
        Args:
            index (int): The 1-based index of the expense in a list for display.
        """
        desc_display = (self.description[:22] + '...') if len(self.description) > 25 else self.description
        cat_display = (self.category[:17] + '...') if len(self.category) > 20 else self.category
        display_timestamp = self.timestamp[:19].replace("T", " ") # YYYY-MM-DD HH:MM:SS

        print(f"{index:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{self.amount:<10.2f} | {cat_display:<20}")

# --- File Handling Functions (Updated for Expense objects) ---

def save_expenses_to_file(all_expenses_list, filename="expenses.txt"):
    """
    Saves the list of Expense objects to a file.
    """
    # Default argument for filename is already in place.
    try:
        with open(filename, "w") as f:
            for expense_obj in all_expenses_list:
                f.write(expense_obj.to_file_string()) # Use the object's method
        print(f"Expenses successfully saved to {filename}")
    except IOError:
        print(f"Error: Could not save expenses to {filename}.")

def load_expenses_from_file(filename="expenses.txt"):
    """
    Loads expenses from a file into a list of Expense objects.
    """
    loaded_expenses_objects = []
    try:
        with open(filename, "r") as f:
            for line in f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                
                parts = stripped_line.split(',', 3)

                if len(parts) == 4:
                    try:
                        description = parts[0]
                        amount_str = parts[1]
                        category = parts[2]
                        timestamp_str = parts[3]
                        
                        # Create an Expense object from the parts
                        expense_obj = Expense(description, float(amount_str), category, timestamp_str)
                        loaded_expenses_objects.append(expense_obj)
                    except ValueError:
                        print(f"Warning: Skipping corrupted line in {filename} (amount not a number): {line.strip()}")
                    except IndexError:
                         print(f"Warning: Skipping malformed line in {filename} (not enough parts): {line.strip()}")
                else:
                    print(f"Warning: Skipping malformed line in {filename} (expected 4 parts, got {len(parts)})")
            print(f"Expenses loaded from {filename}")
    except FileNotFoundError:
        print(f"No previous expenses file found at '{filename}'. Starting fresh.")
    except IOError:
        print(f"Error: Could not read expenses from {filename}.")
    return loaded_expenses_objects

# --- Core Expense Logic Functions (Updated for Expense objects) ---

expenses = [] # Global list will now store Expense objects

def log_expense_details(): # Renamed from log_new_expense for clarity
    """
    Prompts for expense details, creates an Expense object, and returns it.
    Includes practice for default category.
    """
    print("\n--- Log New Expense ---")
    description = input("Enter expense description: ").strip()

    amount = 0.0
    while True:
        try:
            amount_str = input("Enter expense amount (in ₹): ")
            amount = float(amount_str)
            if amount <= 0:
                print("Amount must be positive. Please enter a positive number.")
            else:
                break
        except ValueError:
            print("Invalid amount. Please enter a numeric value (e.g., 150.50).")

    category_input = input("Enter expense category (e.g., Food, Transport, Bills) [Default: General]: ").strip().title()
    # Practice for default parameter:
    if not category_input: # If user just presses Enter
        category = "General"
    else:
        category = category_input
    
    # Create an Expense object (timestamp is handled by __init__)
    new_expense = Expense(description, amount, category)
    
    print(f"Details collected for: '{new_expense.description}'")
    return new_expense

def record_and_store_expenses(number_to_log):
    """Logs a specified number of expenses (as objects) and stores them in the global 'expenses' list."""
    global expenses
    print(f"\n--- Preparing to log {number_to_log} new expenses ---")
    for i in range(number_to_log):
        print(f"\nLogging new expense #{i+1} of {number_to_log}:")
        new_expense_obj = log_expense_details() # Gets an Expense object
        expenses.append(new_expense_obj)       # Append the object
        print(f"Successfully added '{new_expense_obj.description}' to expenses list.")
    print(f"\n--- All {number_to_log} new expenses logged. ---")

def view_all_expenses(all_expenses_list):
    """
    Prints all expenses from the provided list of Expense objects.
    """
    print("\n--- Viewing All Expenses ---")
    if not all_expenses_list:
        print("No expenses recorded yet.")
        return

    header = f"{'#':<3} | {'Timestamp':<26} | {'Description':<25} | {'Amount (₹)':<12} | {'Category':<20}"
    print(header)
    print("-" * len(header))
    
    for idx, expense_obj in enumerate(all_expenses_list):
        expense_obj.display(idx + 1) # Call the object's display method
    print("-" * len(header))

def get_total_expenses(all_expenses_list):
    """
    Calculates the total amount from a list of Expense objects.
    """
    total = 0.0
    for expense_obj in all_expenses_list:
        # Ensure amount is a number, though __init__ should handle this
        if isinstance(expense_obj.amount, (int, float)):
            total += expense_obj.amount
        else:
            print(f"Warning: Expense '{expense_obj.description}' has an invalid amount type.")
    return total

# --- Main Application Execution ---
if __name__ == "__main__":
    expenses_file = "expenses_objects.txt" # Changed filename to reflect object storage
    expenses = load_expenses_from_file(expenses_file) # Initialize with Expense objects

    print(f"\nWelcome to your Personal Finance Tracker CLI (Object-Oriented Version)!")
    print(f"Current System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Loaded {len(expenses)} expenses from '{expenses_file}'.")

    num_expenses_to_log = 0
    while True:
        try:
            num_str = input("\nHow many new expenses would you like to log? (e.g., 2, enter 0 to skip): ")
            num_expenses_to_log = int(num_str)
            if num_expenses_to_log < 0:
                print("Please enter a non-negative number.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a whole number.")

    if num_expenses_to_log > 0:
        record_and_store_expenses(num_expenses_to_log)
    
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