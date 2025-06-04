# app.py
from datetime import datetime
import os # Needed for checking file existence in a more robust way for loading, though try-except is primary

# --- File Handling Functions ---

def save_expenses_to_file(all_expenses_list, filename="expenses.txt"):
    """
    Saves the list of expense dictionaries to a file.
    Each expense is saved as a comma-separated line.
    """
    try:
        with open(filename, "w") as f: # "w" for write mode (overwrites file)
            for expense in all_expenses_list:
                # Ensure all parts are strings before joining, especially amount
                line = f"{expense['description']},{str(expense['amount'])},{expense['category']},{expense['timestamp']}\n"
                f.write(line)
        print(f"Expenses successfully saved to {filename}")
    except IOError:
        print(f"Error: Could not save expenses to {filename}.")

def load_expenses_from_file(filename="expenses.txt"):
    """
    Loads expenses from a file into a list of dictionaries.
    Expects each line to be comma-separated: description,amount,category,timestamp
    """
    loaded_expenses = []
    try:
        with open(filename, "r") as f: # "r" for read mode
            for line in f:
                stripped_line = line.strip()
                if not stripped_line: # Skip empty lines
                    continue
                
                parts = stripped_line.split(',', 3) # Split into exactly 4 parts, the last part can contain commas if description had them
                                                    # A more robust CSV parsing would use the 'csv' module

                if len(parts) == 4:
                    try:
                        description = parts[0]
                        amount = float(parts[1]) # Convert amount back to float
                        category = parts[2]
                        timestamp = parts[3]
                        
                        loaded_expenses.append({
                            "description": description,
                            "amount": amount,
                            "category": category,
                            "timestamp": timestamp
                        })
                    except ValueError:
                        print(f"Warning: Skipping corrupted line in {filename}: {line.strip()} (amount not a number)")
                    except IndexError:
                         print(f"Warning: Skipping malformed line in {filename}: {line.strip()} (not enough parts)")
                else:
                    print(f"Warning: Skipping malformed line in {filename}: {line.strip()} (expected 4 parts, got {len(parts)})")
            print(f"Expenses loaded from {filename}")
    except FileNotFoundError:
        print(f"No previous expenses file found at '{filename}'. Starting fresh.")
    except IOError:
        print(f"Error: Could not read expenses from {filename}.")
    return loaded_expenses

# --- Core Expense Logic Functions ---

# Global list to store all expense dictionaries - will be initialized by loading from file
expenses = [] # This will be overwritten by load_expenses_from_file if successful

def log_expense_details():
    """
    Prompts the user for expense details (description, amount, category),
    validates the amount, adds a timestamp, and returns the expense as a dictionary.
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

    category = input("Enter expense category (e.g., Food, Transport, Bills): ").strip().title()
    current_timestamp = datetime.now().isoformat()

    expense_data = {
        "description": description,
        "amount": amount,
        "category": category,
        "timestamp": current_timestamp
    }
    
    print(f"Details collected for: '{expense_data['description']}'")
    return expense_data

def record_and_store_expenses(number_to_log):
    """Logs a specified number of expenses and stores them in the global 'expenses' list."""
    global expenses # Ensure we are modifying the global list
    print(f"\n--- Preparing to log {number_to_log} new expenses ---")
    for i in range(number_to_log):
        print(f"\nLogging new expense #{i+1} of {number_to_log}:")
        new_expense_dict = log_expense_details()
        expenses.append(new_expense_dict)
        print(f"Successfully added '{new_expense_dict['description']}' to expenses list.")
    print(f"\n--- All {number_to_log} new expenses logged. ---")

def view_all_expenses(current_expenses_list):
    """
    Prints all expenses from the provided list of dictionaries in a formatted way.
    """
    print("\n--- Viewing All Expenses ---")
    if not current_expenses_list:
        print("No expenses recorded yet.")
        return

    header = f"{'#':<3} | {'Timestamp':<26} | {'Description':<25} | {'Amount (₹)':<12} | {'Category':<20}"
    print(header)
    print("-" * len(header))
    
    for idx, expense_dict in enumerate(current_expenses_list):
        description = expense_dict["description"]
        amount = expense_dict["amount"]
        category = expense_dict["category"]
        timestamp = expense_dict["timestamp"]

        desc_display = (description[:22] + '...') if len(description) > 25 else description
        cat_display = (category[:17] + '...') if len(category) > 20 else category
        display_timestamp = timestamp[:19].replace("T", " ")

        print(f"{idx+1:<3} | {display_timestamp:<26} | {desc_display:<25} | ₹{amount:<10.2f} | {cat_display:<20}")
    print("-" * len(header))

def get_total_expenses(current_expenses_list):
    """
    Calculates the total amount of all expenses in the provided list of dictionaries.
    """
    total = 0.0
    for expense_dict in current_expenses_list:
        if "amount" in expense_dict and isinstance(expense_dict["amount"], (int, float)):
            total += expense_dict["amount"]
        else:
            print(f"Warning: Found an expense without a valid 'amount': {expense_dict.get('description', 'N/A')}")
    return total

# --- Main Application Execution ---
if __name__ == "__main__":
    # At the very beginning, load expenses from file
    expenses_file = "expenses_data.txt" # Using a slightly more descriptive filename
    expenses = load_expenses_from_file(expenses_file)

    print(f"\nWelcome to your Personal Finance Tracker CLI!")
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
        record_and_store_expenses(num_expenses_to_log) # This appends to the global 'expenses' list
    
    if expenses: # Only view if there are any expenses (either loaded or newly added)
        view_all_expenses(expenses)
        total_spent = get_total_expenses(expenses)
        print(f"\n--- Total Expenses ---")
        print(f"You have spent a total of: ₹{total_spent:.2f}")
    else:
        print("\nNo expenses recorded to display or total.")

    # After all operations, save the current state of expenses back to the file
    if expenses: # Only save if there are expenses
        save_expenses_to_file(expenses, expenses_file)
    else:
        # Optional: if expenses list is empty, you might want to save an empty file
        # or delete the old one to reflect no expenses. For now, we only save if not empty.
        print("No expenses to save.")
        
    print("\nExiting application.")