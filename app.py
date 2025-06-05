# app.py
from datetime import datetime
import os
# Import classes from the models module within the finance_tracker package
from finance_tracker.models import Expense, RecurringExpense, User

# --- File Handling Functions (Updated for User's Expenses) ---

def save_expenses_to_file(user_object, filename="expenses_user.txt"): # Takes user_object
    """
    Saves the expenses of a given User object to a file.
    """
    if not hasattr(user_object, 'expenses'):
        print(f"Error: User object for '{user_object.username}' does not have an 'expenses' attribute.")
        return

    try:
        with open(filename, "w") as f:
            for expense_obj in user_object.expenses: # Save from user_object.expenses
                f.write(expense_obj.to_file_string())
        print(f"Expenses for user '{user_object.username}' successfully saved to {filename}")
    except IOError:
        print(f"Error: Could not save expenses to {filename}.")

def load_expenses_from_file(filename="expenses_user.txt"): # Name updated for clarity
    """
    Loads expenses from a file, returning a list of Expense or RecurringExpense objects.
    (This function's core logic remains the same, it still just returns a list of objects)
    """
    loaded_expense_objects = []
    try:
        with open(filename, "r") as f:
            for line_number, line in enumerate(f, 1):
                stripped_line = line.strip()
                if not stripped_line: continue
                
                parts = stripped_line.split(',')
                expense_type = parts[0]
                try:
                    if expense_type == Expense.EXPENSE_TYPE and len(parts) == 5:
                        description, amount_str, category, timestamp_str = parts[1], parts[2], parts[3], parts[4]
                        expense_obj = Expense(description, float(amount_str), category, timestamp_str)
                        loaded_expense_objects.append(expense_obj)
                    elif expense_type == RecurringExpense.EXPENSE_TYPE and len(parts) == 6:
                        description, amount_str, category, timestamp_str, recurrence_period = parts[1], parts[2], parts[3], parts[4], parts[5]
                        expense_obj = RecurringExpense(description, float(amount_str), category, recurrence_period, timestamp_str)
                        loaded_expense_objects.append(expense_obj)
                    else:
                        print(f"Warning: Skipping malformed line #{line_number} in {filename}: Unknown type or incorrect parts. Line: '{line.strip()}'")
                except ValueError:
                    print(f"Warning: Skipping corrupted data on line #{line_number} in {filename} (amount not a number): '{line.strip()}'")
                except IndexError:
                     print(f"Warning: Skipping malformed line #{line_number} in {filename} (not enough parts for type '{expense_type}'): '{line.strip()}'")
        if loaded_expense_objects:
            print(f"Successfully parsed {len(loaded_expense_objects)} expense objects from {filename}")
        else:
            print(f"No valid expense data found in {filename} or file was empty.")
    except FileNotFoundError:
        print(f"No previous expenses file found at '{filename}'.") # Message tweaked
    except IOError:
        print(f"Error: Could not read expenses from {filename}.")
    return loaded_expense_objects

# --- Core Expense Logic Functions (Simplified or adapted) ---

def log_standard_expense_details(): # This function can stay as it just creates an object
    """ Prompts for standard expense details, creates an Expense object, and returns it. """
    print("\n--- Log New Standard Expense ---")
    description = input("Enter expense description: ").strip()
    amount = 0.0
    while True:
        try:
            amount_str = input("Enter expense amount (in ₹): ")
            amount = float(amount_str)
            if amount <= 0: print("Amount must be positive.")
            else: break
        except ValueError: print("Invalid amount. Please enter a numeric value.")
    category_input = input("Enter expense category (e.g., Food, Bills) [Default: General]: ").strip().title()
    category = category_input if category_input else "General"
    new_expense = Expense(description, amount, category)
    print(f"Standard Expense Details Logged: {new_expense.description}")
    return new_expense

def log_recurring_expense_details(): # Added for completeness
    """ Prompts for recurring expense details, creates a RecurringExpense object, and returns it. """
    print("\n--- Log New Recurring Expense ---")
    description = input("Enter expense description: ").strip()
    amount = 0.0
    while True:
        try:
            amount_str = input("Enter expense amount (in ₹): ")
            amount = float(amount_str)
            if amount <= 0: print("Amount must be positive.")
            else: break
        except ValueError: print("Invalid amount. Please enter a numeric value.")
    category_input = input("Enter expense category (e.g., Subscription, Rent) [Default: Subscription]: ").strip().title()
    category = category_input if category_input else "Subscription"
    recurrence_period = input("Enter recurrence period (e.g., Monthly, Yearly): ").strip().title()
    if not recurrence_period: recurrence_period = "Monthly" # Default period

    new_recurring_expense = RecurringExpense(description, amount, category, recurrence_period)
    print(f"Recurring Expense Details Logged: {new_recurring_expense.description}")
    return new_recurring_expense


# The global 'view_all_expenses' and 'get_total_expenses' are now methods of the User class.
# The 'record_and_store_expenses' function is also implicitly handled by adding to user.expenses

# --- Main Application Execution ---
if __name__ == "__main__":
    # 1. Create the current_user object
    # Replace "YourName" and "youremail@example.com" with actual desired values
    current_user = User(username="TestUser", email="test@example.com")
    print(f"\nWelcome, {current_user.username}, to your Personal Finance Tracker!")
    print(f"User details: {current_user}") # Uses __str__ from User class
    
    # 2. Define the filename for this user's expenses
    # For simplicity, you could use current_user.username or user_id in filename
    # For now, a generic name as requested:
    user_expenses_file = "expenses_data_user.txt" # Changed from "expenses_user.txt" to avoid old file format confusion if any

    # 3. Load expenses from file and add them to the current_user
    print(f"\nLoading expenses for {current_user.username} from '{user_expenses_file}'...")
    loaded_expense_objects = load_expenses_from_file(user_expenses_file)
    if loaded_expense_objects:
        for exp_obj in loaded_expense_objects:
            current_user.add_expense(exp_obj) # Add to user's internal list
        print(f"{len(loaded_expense_objects)} expenses loaded into {current_user.username}'s account.")
    
    print(f"\nCurrent System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Logging new expenses
    while True:
        log_choice = input("\nLog a new expense? (s for standard, r for recurring, n for no): ").strip().lower()
        if log_choice == 's':
            new_expense = log_standard_expense_details()
            current_user.add_expense(new_expense)
        elif log_choice == 'r':
            new_recurring_expense = log_recurring_expense_details()
            current_user.add_expense(new_recurring_expense)
        elif log_choice == 'n':
            break
        else:
            print("Invalid choice. Please enter 's', 'r', or 'n'.")

    # View and total expenses using User object's methods
    if current_user.expenses:
        current_user.view_expenses() # Calls User.view_expenses()
        total_spent = current_user.get_total_expenses() # Calls User.get_total_expenses()
        print(f"\n--- Total Expenses for {current_user.username} ---")
        print(f"You have spent a total of: ₹{total_spent:.2f}")
    else:
        print(f"\nNo expenses recorded for {current_user.username} to display or total.")

    # Save the current_user's expenses to the file
    if current_user.expenses:
        save_expenses_to_file(current_user, user_expenses_file) # Pass current_user object
    else:
        # If there are no expenses, we might still want to save an empty file
        # to overwrite any old data if that's the desired behavior.
        # For now, only saving if there are expenses.
        print(f"No expenses for {current_user.username} to save.")
        # To ensure an old file doesn't persist if all expenses are deleted,
        # you could explicitly save an empty list or delete the file:
        # save_expenses_to_file(current_user, user_expenses_file) # Will save an empty file if user.expenses is empty

    print("\nExiting application.")