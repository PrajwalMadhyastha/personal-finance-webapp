# app.py

# Global list to store all expense dictionaries
expenses = []

def log_expense_details():
    """
    Prompts the user for expense details (description, amount, category),
    validates the amount, and returns the expense as a dictionary.
    """
    print("\n--- Log New Expense (as Dictionary) ---")
    description = input("Enter expense description: ").strip()

    amount = 0.0
    while True:
        try:
            amount_str = input("Enter expense amount (in ₹): ")
            amount = float(amount_str)
            if amount <= 0:
                print("Amount must be positive. Please enter a positive number.")
            else:
                break  # Valid amount entered, exit loop
        except ValueError:
            print("Invalid input. Please enter a numeric value for the amount (e.g., 150.50).")

    category = input("Enter expense category (e.g., Food, Transport, Bills): ").strip().title()

    # Create and return a dictionary
    expense_data = {
        "description": description,
        "amount": amount,
        "category": category
    }
    
    print(f"Details collected for: '{expense_data['description']}'")
    return expense_data

def record_and_store_expenses(number_to_log):
    """Logs a specified number of expenses and stores them as dictionaries in the global 'expenses' list."""
    print(f"\n--- Preparing to log {number_to_log} expenses (as Dictionaries) ---")
    for i in range(number_to_log):
        print(f"\nLogging expense #{i+1} of {number_to_log}:")
        new_expense_dict = log_expense_details()  # Get the dictionary
        expenses.append(new_expense_dict)         # Append it to the global list
        print(f"Successfully added '{new_expense_dict['description']}' to expenses list.")
    print(f"\n--- All {number_to_log} expenses logged and stored as dictionaries. ---")

def view_all_expenses(current_expenses_list):
    """
    Prints all expenses from the provided list of dictionaries in a formatted way.
    Currency is displayed in Rupees (₹).
    """
    print("\n--- Viewing All Expenses (from Dictionaries) ---")
    if not current_expenses_list:
        print("No expenses recorded yet.")
        return

    print(f"{'#':<3} | {'Description':<30} | {'Amount (₹)':<12} | {'Category':<20}")
    print("-" * 75) 
    for idx, expense_dict in enumerate(current_expenses_list):
        # Access dictionary values by keys
        description = expense_dict["description"]
        amount = expense_dict["amount"]
        category = expense_dict["category"]

        desc_display = (description[:27] + '...') if len(description) > 30 else description
        cat_display = (category[:17] + '...') if len(category) > 20 else category
        
        print(f"{idx+1:<3} | {desc_display:<30} | ₹{amount:<10.2f} | {cat_display:<20}")
    print("-" * 75)

def get_total_expenses(current_expenses_list):
    """
    Calculates the total amount of all expenses in the provided list of dictionaries.
    """
    total = 0.0
    for expense_dict in current_expenses_list:
        total += expense_dict["amount"] # Access the 'amount' key
    return total

# app.py (Continuing from your existing dictionary-based version)

# ... (all your other functions: log_expense_details, record_and_store_expenses, view_all_expenses) ...

# (The get_total_expenses function definition from above goes here)
def get_total_expenses(current_expenses_list):
    """
    Calculates the total amount of all expenses in the provided list of dictionaries.
    Each dictionary is expected to have an "amount" key.
    """
    total = 0.0
    for expense_dict in current_expenses_list:
        if "amount" in expense_dict and isinstance(expense_dict["amount"], (int, float)):
            total += expense_dict["amount"]
        else:
            print(f"Warning: Found an expense without a valid amount: {expense_dict.get('description', 'N/A')}")
    return total

# --- Main part of your script to run examples ---
if __name__ == "__main__":
    print("Welcome to your Personal Finance Tracker CLI (Dictionary Version - India)!")

    num_expenses_to_log = 0
    while True:
        try:
            num_str = input("How many expenses would you like to log? (e.g., 2, enter 0 to skip): ")
            num_expenses_to_log = int(num_str)
            if num_expenses_to_log < 0:
                print("Please enter a non-negative number.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a whole number.")

    if num_expenses_to_log > 0:
        record_and_store_expenses(num_expenses_to_log)
    
    # View all expenses (passing the global 'expenses' list which contains dictionaries)
    view_all_expenses(expenses)
    
    # Get and print the total expenses
    if expenses:
        total_spent = get_total_expenses(expenses)
        print(f"\n--- Total Expenses (from Dictionaries) ---")
        print(f"You have spent a total of: ₹{total_spent:.2f}")
    else:
        print("\nNo expenses to total.")

    if expenses:  # Check if there are any expenses to total
        total_spent = get_total_expenses(expenses) # Call the function
        print(f"\n--- Total Expenses ---")
        print(f"You have spent a total of: ₹{total_spent:.2f}") # Using Rupee symbol
    elif not expenses and 'num_expenses_to_log' in locals() and num_expenses_to_log > 0:
        # This case might occur if logging was attempted but resulted in an empty expenses list
        print("\nNo valid expenses were recorded to calculate a total.")
    else:
        # This case if no attempt to log expenses was made or if num_expenses_to_log was 0
        print("\nNo expenses recorded yet to calculate a total.")
        
    print("\nExiting application.")