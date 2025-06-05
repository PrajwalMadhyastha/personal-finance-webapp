from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World! This is my Personal Finance App homepage.'

# Define another route
@app.route('/about')
def about_page():
    return 'This is the about page for the finance app.'

# This block ensures the app runs only when the script is executed directly
# (and not when imported as a module by another script)
if __name__ == '__main__':
    app.run(debug=True) # debug=True is helpful for development

# # app.py
# from datetime import datetime
# import os
# import json # Import the json module
# from finance_tracker.models import Expense, RecurringExpense, User

# # --- File Handling Functions (Updated for JSON) ---

# def save_expenses_to_file(user_object, filename="user_expenses.json"): # Changed filename
#     """
#     Saves the expenses of a given User object to a JSON file.
#     """
#     if not hasattr(user_object, 'expenses'):
#         print(f"Error: User object for '{user_object.username}' does not have an 'expenses' attribute.")
#         return

#     # List comprehension to convert all expense objects to dictionaries
#     expenses_as_dicts = [expense_obj.to_dict() for expense_obj in user_object.expenses]

#     try:
#         with open(filename, "w") as f:
#             json.dump(expenses_as_dicts, f, indent=4) # Use json.dump
#         print(f"Expenses for user '{user_object.username}' successfully saved to {filename}")
#     except IOError:
#         print(f"Error: Could not save expenses to {filename}.")
#     except TypeError as e: # Catch errors if objects are not serializable (should be handled by to_dict)
#         print(f"Error serializing expenses to JSON: {e}")


# def load_expenses_from_file(filename="user_expenses.json"): # Changed filename
#     """
#     Loads expenses from a JSON file, creating Expense or RecurringExpense objects.
#     """
#     loaded_expense_objects = []
#     try:
#         with open(filename, "r") as f:
#             data = json.load(f) # Load the entire JSON structure (list of dicts)
            
#             if not isinstance(data, list):
#                 print(f"Warning: Data in {filename} is not a list. Skipping load.")
#                 return []

#             for expense_dict in data:
#                 if not isinstance(expense_dict, dict):
#                     print(f"Warning: Found non-dictionary item in {filename}. Skipping item: {expense_dict}")
#                     continue

#                 expense_type = expense_dict.get("expense_type") # Get the type
                
#                 try:
#                     # Common fields
#                     description = expense_dict.get("description")
#                     amount = float(expense_dict.get("amount", 0)) # Default to 0 if amount is missing
#                     category = expense_dict.get("category")
#                     timestamp = expense_dict.get("timestamp")

#                     if not all([description, category, timestamp]): # Basic validation
#                         print(f"Warning: Missing essential fields in expense data: {expense_dict}. Skipping.")
#                         continue

#                     if expense_type == Expense.EXPENSE_TYPE:
#                         expense_obj = Expense(description, amount, category, timestamp)
#                         loaded_expense_objects.append(expense_obj)
#                     elif expense_type == RecurringExpense.EXPENSE_TYPE:
#                         recurrence_period = expense_dict.get("recurrence_period")
#                         if not recurrence_period:
#                             print(f"Warning: Missing 'recurrence_period' for recurring expense: {expense_dict}. Skipping.")
#                             continue
#                         expense_obj = RecurringExpense(description, amount, category, recurrence_period, timestamp)
#                         loaded_expense_objects.append(expense_obj)
#                     else:
#                         print(f"Warning: Unknown expense type '{expense_type}' in {filename}. Skipping item: {expense_dict}")
                
#                 except (ValueError, TypeError) as e: # Catch issues with float conversion or missing keys if .get wasn't used carefully
#                     print(f"Warning: Corrupted data for an expense in {filename}. Details: {e}. Item: {expense_dict}. Skipping.")

#         if loaded_expense_objects:
#             print(f"Successfully parsed {len(loaded_expense_objects)} expense objects from {filename}")
#         elif data: # File was loaded but no valid objects were created
#             print(f"No valid expense objects could be created from data in {filename}.")
#         else: # File was empty or json.load returned an empty list
#              print(f"No expense data found in {filename} or file was empty.")


#     except FileNotFoundError:
#         print(f"No previous expenses file found at '{filename}'.")
#     except json.JSONDecodeError: # Handle malformed JSON
#         print(f"Error: Could not decode JSON from {filename}. File might be corrupted or empty.")
#     except IOError:
#         print(f"Error: Could not read expenses from {filename}.")
#     return loaded_expense_objects

# # --- Core Expense Logic Functions (log_standard_expense_details, log_recurring_expense_details) ---
# # These remain largely the same as they create and return objects.

# def log_standard_expense_details():
#     print("\n--- Log New Standard Expense ---")
#     description = input("Enter expense description: ").strip()
#     amount = 0.0
#     while True:
#         try:
#             amount_str = input("Enter expense amount (in ₹): ")
#             amount = float(amount_str)
#             if amount <= 0: print("Amount must be positive.")
#             else: break
#         except ValueError: print("Invalid amount. Please enter a numeric value.")
#     category_input = input("Enter expense category (e.g., Food, Bills) [Default: General]: ").strip().title()
#     category = category_input if category_input else "General"
#     new_expense = Expense(description, amount, category)
#     print(f"Standard Expense Details Logged: {new_expense.description}")
#     return new_expense

# def log_recurring_expense_details():
#     print("\n--- Log New Recurring Expense ---")
#     description = input("Enter expense description: ").strip()
#     amount = 0.0
#     while True:
#         try:
#             amount_str = input("Enter expense amount (in ₹): ")
#             amount = float(amount_str)
#             if amount <= 0: print("Amount must be positive.")
#             else: break
#         except ValueError: print("Invalid amount. Please enter a numeric value.")
#     category_input = input("Enter expense category (e.g., Subscription, Rent) [Default: Subscription]: ").strip().title()
#     category = category_input if category_input else "Subscription"
#     recurrence_period = input("Enter recurrence period (e.g., Monthly, Yearly): ").strip().title()
#     if not recurrence_period: recurrence_period = "Monthly" 

#     new_recurring_expense = RecurringExpense(description, amount, category, recurrence_period)
#     print(f"Recurring Expense Details Logged: {new_recurring_expense.description}")
#     return new_recurring_expense

# # --- Main Application Execution ---
# if __name__ == "__main__":
#     current_user = User(username="AlphaUser", email="alpha@example.com") # Example User
#     print(f"\nWelcome, {current_user.username}, to your Personal Finance Tracker!")
#     print(f"User details: {current_user}")
    
#     user_expenses_file = f"{current_user.username.lower()}_expenses.json" # User-specific filename

#     print(f"\nLoading expenses for {current_user.username} from '{user_expenses_file}'...")
#     loaded_objects = load_expenses_from_file(user_expenses_file)
#     for obj in loaded_objects:
#         current_user.add_expense(obj) # Silently add, add_expense prints its own confirmation if verbose
    
#     print(f"\nCurrent System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

#     while True:
#         log_choice = input("\nLog a new expense? (s: standard, r: recurring, v: view, f: filter by cat, q: quit): ").strip().lower()
#         if log_choice == 's':
#             new_expense = log_standard_expense_details()
#             current_user.add_expense(new_expense)
#         elif log_choice == 'r':
#             new_recurring_expense = log_recurring_expense_details()
#             current_user.add_expense(new_recurring_expense)
#         elif log_choice == 'v':
#             current_user.view_expenses()
#         elif log_choice == 'f':
#             cat_to_filter = input("Enter category to filter by: ")
#             filtered = current_user.get_expenses_by_category(cat_to_filter)
#             if filtered:
#                 print(f"\n--- Expenses in Category: {cat_to_filter.title()} ---")
#                 header = f"{'#':<3} | {'Timestamp':<26} | {'Description':<25} | {'Amount (₹)':<12} | {'Category':<20} | {'Recurrence':<15}"
#                 print(header)
#                 print("-" * len(header))
#                 for idx, exp_obj in enumerate(filtered):
#                     exp_obj.display(idx + 1)
#                 print("-" * len(header))
#             else:
#                 print(f"No expenses found in category: {cat_to_filter.title()}")
#         elif log_choice == 'q':
#             break
#         else:
#             print("Invalid choice. Please try again.")

#     if current_user.expenses:
#         # view_expenses already called if user chose 'v'
#         total_spent = current_user.get_total_expenses()
#         print(f"\n--- Total Expenses for {current_user.username} ---")
#         print(f"You have spent a total of: ₹{total_spent:.2f}")
#         save_expenses_to_file(current_user, user_expenses_file)
#     else:
#         print(f"\nNo expenses recorded for {current_user.username} to display or total.")
#         # Optionally save an empty list to clear the file if desired
#         # save_expenses_to_file(current_user, user_expenses_file) 
        
#     print("\nExiting application.")