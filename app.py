# app.py

# Global list to store all expense dictionaries
expenses = []

def log_new_expense_details():
    """
    Prompts the user for expense details (description, amount, category),
    validates the amount, and returns the expense as a dictionary.
    """
    print("\n--- Log New Expense ---")
    description = input("Enter expense description: ").strip()

    amount = 0.0
    while True:
        try:
            amount_str = input("Enter expense amount: ")
            amount = float(amount_str)
            if amount <= 0:
                print("Amount must be positive. Please enter a positive number.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a numeric value for the amount (e.g., 50.75).")

    category = input("Enter expense category (e.g., Food, Transport, Bills): ").strip().title()

    expense_data = {
        "description": description,
        "amount": amount,
        "category": category
    }
    
    print(f"Details collected for: '{expense_data['description']}'")
    if expense_data['category'] == "Food": # Example of category-specific message after collection
        print("Insight: Remember to track your grocery bills!")
    # Add more category-specific insights if desired

    return expense_data

def record_and_store_expenses(number_to_log):
    """Logs a specified number of expenses and stores them in the global 'expenses' list."""
    print(f"\n--- Preparing to log {number_to_log} expenses ---")
    for i in range(number_to_log):
        print(f"\nLogging expense #{i+1} of {number_to_log}:")
        new_expense = log_new_expense_details() # Get the dictionary
        expenses.append(new_expense)            # Append it to the global list
        print(f"Successfully added '{new_expense['description']}' to expenses list.")
    print(f"\n--- All {number_to_log} expenses logged and stored. ---")

def view_all_expenses(current_expenses_list):
    """
    Prints all expenses from the provided list in a formatted way.
    """
    print("\n--- Viewing All Expenses ---")
    if not current_expenses_list:
        print("No expenses recorded yet.")
        return

    print(f"{'#':<3} | {'Description':<30} | {'Amount':<10} | {'Category':<20}")
    print("-" * 70)
    for idx, expense in enumerate(current_expenses_list):
        # Ensure description isn't too long for the formatted output
        desc_display = (expense['description'][:27] + '...') if len(expense['description']) > 30 else expense['description']
        cat_display = (expense['category'][:17] + '...') if len(expense['category']) > 20 else expense['category']
        print(f"{idx+1:<3} | {desc_display:<30} | ${expense['amount']:<9.2f} | {cat_display:<20}")
    print("-" * 70)

def get_total_expenses(current_expenses_list):
    """
    Calculates the total amount of all expenses in the provided list.
    """
    total = 0.0
    for expense in current_expenses_list:
        total += expense["amount"]
    return total

# --- Main part of your script to run examples ---
if __name__ == "__main__":
    print("Welcome to your Personal Finance Tracker CLI!")

    # Log a few expenses
    num_expenses_to_log = int(input("How many expenses would you like to log? (e.g., 2): "))
    if num_expenses_to_log > 0:
        record_and_store_expenses(num_expenses_to_log)
    
    # View all expenses
    # The 'expenses' list is global, so we pass it directly
    view_all_expenses(expenses)

    # Get and print the total expenses
    if expenses: # Only calculate total if there are expenses
        total_spent = get_total_expenses(expenses)
        print(f"\n--- Total Expenses ---")
        print(f"You have spent a total of: ${total_spent:.2f}")
    else:
        print("\nNo expenses to total.")
    
    print("\nExiting application.")