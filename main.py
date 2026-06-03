import json
import os

# FILES


FILES = {
    "customers": "customers.json",
    "inventory": "inventory.json",
    "equipment_units": "equipment_units.json"
}


# JSON FILE HANDLING


def create_file_if_missing(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as file:
            json.dump([], file)


def initialize_files():
    for file in FILES.values():
        create_file_if_missing(file)


def load_data(filename):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except:
        return []


def save_data(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)



# CUSTOMER DETAILS


def add_customer():
    customers = load_data(FILES["customers"])

    customer_id = int(input("Enter Customer ID: "))
    name = input("Enter Customer Name: ")
    phone = input("Enter Phone Number: ")
    address = input("Enter Address: ")

    for customer in customers:
        if customer["customer_id"] == customer_id:
            print("Customer ID already exists!")
            return

    new_customer = {
        "customer_id": customer_id,
        "name": name,
        "phone": phone,
        "address": address
    }

    customers.append(new_customer)
    save_data(FILES["customers"], customers)

    print("Customer added successfully!")


def view_customers():
    customers = load_data(FILES["customers"])

    if not customers:
        print("No customers found.")
        return

    for customer in customers:
        print(customer)


def search_customer():
    customer_id = int(input("Enter Customer ID: "))

    customers = load_data(FILES["customers"])

    for customer in customers:
        if customer["customer_id"] == customer_id:
            print(customer)
            return

    print("Customer not found.")



# INVENTORY 

def add_item():
    inventory = load_data(FILES["inventory"])

    item_id = int(input("Enter Item ID: "))
    item_name = input("Enter Item Name: ")
    category = input("Enter Category: ")
    quantity = int(input("Enter Total Quantity: "))
    rent = float(input("Enter Rent Per Day: "))

    if quantity < 0:
        print("Quantity cannot be negative.")
        return

    for item in inventory:
        if item["item_id"] == item_id:
            print("Item ID already exists.")
            return

    new_item = {
        "item_id": item_id,
        "item_name": item_name,
        "category": category,
        "total_quantity": quantity,
        "rent_per_day": rent
    }

    inventory.append(new_item)
    save_data(FILES["inventory"], inventory)

    print("Item added successfully!")


def view_items():
    inventory = load_data(FILES["inventory"])

    if not inventory:
        print("No items found.")
        return

    for item in inventory:
        print(item)



# EQUIPMENT 


def add_equipment_unit():
    units = load_data(FILES["equipment_units"])

    unit_id = int(input("Enter Unit ID: "))
    item_id = int(input("Enter Item ID: "))
    unit_name = input("Enter Unit Name: ")

    new_unit = {
        "unit_id": unit_id,
        "item_id": item_id,
        "unit_name": unit_name,
        "status": "Available"
    }

    units.append(new_unit)

    save_data(FILES["equipment_units"], units)

    print("Equipment unit added successfully!")


def view_equipment_units():
    units = load_data(FILES["equipment_units"])

    for unit in units:
        print(unit)


# MENU


def main():
    initialize_files()

    while True:
        print("\n===== SHARMA TENT HOUSE =====")
        print("1. Add Customer")
        print("2. View Customers")
        print("3. Search Customer")
        print("4. Add Inventory Item")
        print("5. View Inventory")
        print("6. Add Equipment Unit")
        print("7. View Equipment Units")
        print("0. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            add_customer()

        elif choice == "2":
            view_customers()

        elif choice == "3":
            search_customer()

        elif choice == "4":
            add_item()

        elif choice == "5":
            view_items()

        elif choice == "6":
            add_equipment_unit()

        elif choice == "7":
            view_equipment_units()

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


main()