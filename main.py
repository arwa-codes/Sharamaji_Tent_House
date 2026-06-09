import json
import os

# --- File Operations ---

def load_json(filename):
    """Loads a JSON file or returns an empty list if not found/corrupted."""
    if not os.path.exists(filename):
       
        try:
            with open(filename, 'w') as file:
                json.dump([], file)
            return []
        except Exception as e:
            print(f"Error creating file {filename}: {e}")
            return []
    
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        
        return []

def save_json(filename, data):
    """Saves data into a JSON file with nice formatting."""
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error saving file {filename}: {e}")

# --- Customer Management Functions ---

def add_customer():
    customers = load_json('customers.json')
    
    try:
        cust_id = int(input("\nEnter Customer ID: "))
        
        
        for c in customers:
            if c['customer_id'] == cust_id:
                print(f"Error: Customer ID {cust_id} already exists!")
                return

        name = input("Enter Name: ")
        phone = input("Enter Phone: ")
        address = input("Enter Address: ")

        new_customer = {
            "customer_id": cust_id,
            "name": name,
            "phone": phone,
            "address": address
        }
        
        customers.append(new_customer)
        save_json('customers.json', customers)
        print("Customer added successfully!")
        
    except ValueError:
        print("Invalid input! Customer ID must be a number.")

def view_customers():
    customers = load_json('customers.json')
    
    if not customers:
        print("\nNo customers found.")
        return

    print("\n--- Registered Customers ---")
    for c in customers:
        print(f"ID: {c['customer_id']} | Name: {c['name']} | Phone: {c['phone']} | Address: {c['address']}")

def search_customer():
    customers = load_json('customers.json')
    query = input("\nEnter name or ID to search: ").lower()
    
    results = []
    for c in customers:
        if query in str(c['customer_id']) or query in c['name'].lower():
            results.append(c)
            
    if results:
        print("\n--- Search Results ---")
        for r in results:
            print(f"ID: {r['customer_id']} | Name: {r['name']} | Phone: {r['phone']}")
    else:
        print("No matching customer found.")

# --- Inventory Management Functions ---

def add_inventory_item():
    inventory = load_json('inventory.json')
    
    try:
        item_id = int(input("\nEnter Item ID: "))
        
      
        for item in inventory:
            if item['item_id'] == item_id:
                print(f"Error: Item ID {item_id} already exists!")
                return

        name = input("Enter Item Name: ")
        category = input("Enter Category: ")
        qty = int(input("Enter Total Quantity: "))
        rent = float(input("Enter Rent Per Day: "))

        new_item = {
            "item_id": item_id,
            "name": name,
            "category": category,
            "total_quantity": qty,
            "rent_per_day": rent
        }
        
        inventory.append(new_item)
        save_json('inventory.json', inventory)
        print(f"Item '{name}' added to inventory!")
        
    except ValueError:
        print("Invalid input! Please enter numbers for ID, Quantity, and Rent.")

def view_inventory():
    inventory = load_json('inventory.json')
    
    if not inventory:
        print("\nInventory is empty.")
        return

    print("\n--- Inventory List ---")
    for item in inventory:
        print(f"ID: {item['item_id']} | Name: {item['name']} | Qty: {item['total_quantity']} | Rent: ₹{item['rent_per_day']}")

def update_inventory_item():
    inventory = load_json('inventory.json')
    
    try:
        search_id = int(input("\nEnter Item ID to update: "))
        
        found_item = None
        for item in inventory:
            if item['item_id'] == search_id:
                found_item = item
                break
        
        if not found_item:
            print("Error: Item ID not found!")
            return

        print(f"Updating '{found_item['name']}'. Leave blank to keep current value.")
        
        new_name = input(f"New Name [{found_item['name']}]: ")
        if new_name: found_item['name'] = new_name
        
        new_cat = input(f"New Category [{found_item['category']}]: ")
        if new_cat: found_item['category'] = new_cat
        
        new_qty = input(f"New Quantity [{found_item['total_quantity']}]: ")
        if new_qty: found_item['total_quantity'] = int(new_qty)
        
        new_rent = input(f"New Rent [{found_item['rent_per_day']}]: ")
        if new_rent: found_item['rent_per_day'] = float(new_rent)

        save_json('inventory.json', inventory)
        print("Item updated successfully!")
        
    except ValueError:
        print("Invalid input! Please enter correct numeric values.")

# --- Equipment Unit Management Functions ---

def add_equipment_unit():
    units = load_json('equipment_units.json')
    inventory = load_json('inventory.json')
    
    try:
        unit_id = input("\nEnter Unit ID (e.g., UNIT-001): ").strip()
        
        
        for u in units:
            if u['unit_id'].lower() == unit_id.lower():
                print(f"Error: Unit ID '{unit_id}' already exists!")
                return
        
        item_id = int(input("Enter associated Item ID from inventory: "))
        
        
        item_exists = False
        for item in inventory:
            if item['item_id'] == item_id:
                item_exists = True
                break
        
        if not item_exists:
            print(f"Error: Item ID {item_id} does not exist in inventory. Please add it first.")
            return

        unit_name = input("Enter Unit Name: ")
        status = input("Enter Status (Available/Maintenance): ") or "Available"

        new_unit = {
            "unit_id": unit_id,
            "item_id": item_id,
            "unit_name": unit_name,
            "status": status
        }
        
        units.append(new_unit)
        save_json('equipment_units.json', units)
        print("Equipment unit added successfully!")
        
    except ValueError:
        print("Invalid Input! Item ID must be a number.")

def view_equipment_units():
    units = load_json('equipment_units.json')
    
    if not units:
        print("\nNo equipment units recorded.")
        return

    print("\n--- Equipment Units Status ---")
    for u in units:
        print(f"Unit ID: {u['unit_id']} | Item ID: {u['item_id']} | Name: {u['unit_name']} | Status: {u['status']}")

def change_unit_status():
    units = load_json('equipment_units.json')
    unit_id = input("Enter Unit ID to change status: ").strip()
    
    found = False
    for u in units:
        if u['unit_id'].lower() == unit_id.lower():
            print(f"Current Status: {u['status']}")
            new_status = input("Enter new status (Available/Maintenance/Broken): ")
            if new_status:
                u['status'] = new_status
                found = True
            break
            
    if found:
        save_json('equipment_units.json', units)
        print("Unit status updated successfully!")
    else:
        print("Error: Unit ID not found.")

# --- Main Program Menu ---

def main_menu():
    while True:
        print("\n==============================================")
        print("   SHARMAJI TENT HOUSE - MANAGEMENT SYSTEM   ")
        print("==============================================")
        print("1. Customer Management")
        print("2. Inventory Management")
        print("3. Equipment Unit Management")
        print("4. Exit")
        
        choice = input("\nSelect an Option (1-4): ")

        if choice == '1':
            customer_menu()
        elif choice == '2':
            inventory_menu()
        elif choice == '3':
            equipment_menu()
        elif choice == '4':
            print("Thank you for using the system. Goodbye!")
            break
        else:
            print("Invalid choice, please select 1-4.")

def customer_menu():
    while True:
        print("\n--- Customer Management ---")
        print("1. Add Customer")
        print("2. View All Customers")
        print("3. Search for Customer")
        print("4. Back to Main Menu")
        
        choice = input("Select an Option: ")
        
        if choice == '1': add_customer()
        elif choice == '2': view_customers()
        elif choice == '3': search_customer()
        elif choice == '4': break
        else: print("Invalid selection.")

def inventory_menu():
    while True:
        print("\n--- Inventory Management ---")
        print("1. Add Item to Inventory")
        print("2. View Inventory List")
        print("3. Update Item Details")
        print("4. Back to Main Menu")
        
        choice = input("Select an Option: ")
        
        if choice == '1': add_inventory_item()
        elif choice == '2': view_inventory()
        elif choice == '3': update_inventory_item()
        elif choice == '4': break
        else: print("Invalid selection.")

def equipment_menu():
    while True:
        print("\n--- Equipment Unit Management ---")
        print("1. Add Equipment Unit")
        print("2. View Unit Status")
        print("3. Change Unit Status")
        print("4. Back to Main Menu")
        
        choice = input("Select an Option: ")
        
        if choice == '1': add_equipment_unit()
        elif choice == '2': view_equipment_units()
        elif choice == '3': change_unit_status()
        elif choice == '4': break
        else: print("Invalid selection.")

if __name__ == "__main__":
    main_menu()




















































