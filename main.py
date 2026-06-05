```python
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

    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        print(f"Error: {filename} contains invalid data.")
        return []

def save_data(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

# CUSTOMER DETAILS

def add_customer():
    customers = load_data(FILES["customers"])

    try:
        customer_id = int(input("Enter Customer ID: "))
    except ValueError:
        print("Invalid Customer ID.")
        return

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
        print("\n------------------")
        print("Customer ID :", customer["customer_id"])
        print("Name        :", customer["name"])
        print("Phone       :", customer["phone"])
        print("Address     :", customer["address"])

def search_customer():
    try:
        customer_id = int(input("Enter Customer ID: "))
    except ValueError:
        print("Invalid Customer ID.")
        return

    customers = load_data(FILES["customers"])

    for customer in customers:
        if customer["customer_id"] == customer_id:
            print("\nCustomer Found")
            print(customer)
            return

    print("Customer not found.")

# INVENTORY

def add_item():
    inventory = load_data(FILES["inventory"])

    try:
        item_id = int(input("Enter Item ID: "))
        quantity = int(input("Enter Total Quantity: "))
        rent = float(input("Enter Rent Per Day: "))
    except ValueError:
        print("Invalid input.")
        return

    item_name = input("Enter Item Name: ")
    category = input("Enter Category: ")

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
        print("\n------------------")
        print("Item ID      :", item["item_id"])
        print("Item Name    :", item["item_name"])
        print("Category     :", item["category"])
        print("Quantity     :", item["total_quantity"])
        print("Rent Per Day :", item["rent_per_day"])

def update_item():
    try:
        item_id = int(input("Enter Item ID: "))
    except ValueError:
        print("Invalid Item ID.")
        return

    inventory = load_data(FILES["inventory"])

    for item in inventory:

        if item["item_id"] == item_id:

            item["item_name"] = input("Enter New Item Name: ")
            item["category"] = input("Enter New Category: ")

            try:
                item["total_quantity"] = int(input("Enter New Quantity: "))
                item["rent_per_day"] = float(input("Enter New Rent Per Day: "))
            except ValueError:
                print("Invalid input.")
                return

            save_data(FILES["inventory"], inventory)

            print("Item updated successfully!")
            return

    print("Invalid Item ID.")

# EQUIPMENT

def add_equipment_unit():
    units = load_data(FILES["equipment_units"])
    inventory = load_data(FILES["inventory"])

    try:
        unit_id = int(input("Enter Unit ID: "))
        item_id = int(input("Enter Item ID: "))
    except ValueError:
        print("Invalid ID.")
        return

    for unit in units:
        if unit["unit_id"] == unit_id:
            print("Unit ID already exists.")
            return

    item_found = False

    for item in inventory:
        if item["item_id"] == item_id:
            item_found = True
            break

    if not item_found:
        print("Invalid Item ID.")
        return

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

    if not units:
        print("No units found.")
        return

    for unit in units:
        print("\n------------------")
        print("Unit ID   :", unit["unit_id"])
        print("Item ID   :", unit["item_id"])
        print("Unit Name :", unit["unit_name"])
        print("Status    :", unit["status"])

def change_unit_status():

    try:
        unit_id = int(input("Enter Unit ID: "))
    except ValueError:
        print("Invalid Unit ID.")
        return

    units = load_data(FILES["equipment_units"])

    for unit in units:

        if unit["unit_id"] == unit_id:

            print("1. Available")
            print("2. Rented")
            print("3. Maintenance")

            choice = input("Enter choice: ")

            if choice == "1":
                unit["status"] = "Available"

            elif choice == "2":
                unit["status"] = "Rented"

            elif choice == "3":
                unit["status"] = "Maintenance"

            else:
                print("Invalid choice.")
                return

            save_data(FILES["equipment_units"], units)

            print("Status updated successfully!")
            return

    print("Unit ID not found.")

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
        print("8. Update Item")
        print("9. Change Unit Status")
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

        elif choice == "8":
            update_item()

        elif choice == "9":
            change_unit_status()

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")

main()
```
