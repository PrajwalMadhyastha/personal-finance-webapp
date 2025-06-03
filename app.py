try:
    category = input("Enter expense category: ")
except ValueError:
    print("Invalid category. Please enter a category.")
    category = ''

if category.lower() == "food":
    print("Remember to track your grocery bills!")
elif category.lower() == "transport":
    print("Remember to track your commut expenses!")
elif category.lower() == "entertainment":
    print("Remember to track your Entertainment bills!")

try:
    amount = float(input("Enter expense amount: "))
except ValueError:
    print("Invalid amount. Please enter a number.")
    amount = 0

if amount <= 0:
    print("Amount is not greater than zero")

categories = ['Food', 'Transport', 'Bills']

for i in categories:
    print(i)

def greet_user(name):
    print("Hello " + name)

def log_new_expense(category, amount, description):
    return ("Category is " + category + "Description is " + description + "and the Amount is " + amount)

