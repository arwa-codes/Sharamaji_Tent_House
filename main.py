import json
import os
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

# --- File Operations ---

# --- Helper Functions ---

def load_json(filename):
    """Loads a JSON file or returns an empty list if not found. Reports error if corrupted."""
    if not os.path.exists(filename):
        return []
    
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            # Re-convert numeric strings to Decimal where needed
            if "inventory.json" in filename:
                for item in data:
                    item['rent_per_day'] = Decimal(item.get('rent_per_day', 0))
            return data
    except json.JSONDecodeError:
        print(f"\n[ERROR] File '{filename}' is corrupted and cannot be loaded.")
        return None
    except Exception as e:
        print(f"\n[ERROR] Could not read '{filename}': {e}")
        return []

def save_json(filename, data):
    """Saves data into a JSON file with Decimal support and nice formatting."""
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4, cls=DecimalEncoder)
    except Exception as e:
        print(f"\n[ERROR] Could not save to '{filename}': {e}")

def generate_id(prefix, data, key):
    """Auto-generates the next ID (e.g., C101, C102)."""
    if not data:
        return f"{prefix}101"
    
    ids = []
    for item in data:
        val = str(item.get(key, ""))
        if val.startswith(prefix):
            try:
                num = int(val[len(prefix):])
                ids.append(num)
            except ValueError:
                continue
    
    next_num = max(ids) + 1 if ids else 101
    return f"{prefix}{next_num}"

# --- Customer Management Functions ---

def add_customer():
    customers = load_json('customers.json')
    if customers is None: return # Stop if file is corrupted

    print("\n--- Register New Customer ---")
    cust_id = generate_id("C", customers, "customer_id")
    print(f"Generated Customer ID: {cust_id}")

    name = input("Enter Name: ").strip()
    if not name:
        print("[ERROR] Customer name cannot be empty.")
        return
        
    phone = input("Enter Phone: ").strip()
    address = input("Enter Address: ").strip()

    new_customer = {
        "customer_id": cust_id,
        "name": name,
        "phone": phone,
        "address": address
    }
    
    customers.append(new_customer)
    save_json('customers.json', customers)
    print(f"[SUCCESS] Customer '{name}' added with ID: {cust_id}")

def view_customers():
    customers = load_json('customers.json')
    if not customers:
        if customers is None: return
        print("\nNo customers found.")
        return

    print("\n" + "="*80)
    print(f"{'ID':<8} | {'Name':<25} | {'Phone':<15} | {'Address':<25}")
    print("-" * 80)
    for c in customers:
        print(f"{c['customer_id']:<8} | {c['name']:<25} | {c['phone']:<15} | {c['address']:<25}")
    print("="*80)

def search_customer():
    customers = load_json('customers.json')
    if not customers:
        if customers is None: return
        print("\nNo customers available to search.")
        return

    query = input("\nEnter name or ID to search: ").lower()
    results = [c for c in customers if query in str(c['customer_id']).lower() or query in c['name'].lower()]
            
    if results:
        print("\n--- Search Results ---")
        print(f"{'ID':<8} | {'Name':<25} | {'Phone':<15}")
        print("-" * 55)
        for r in results:
            print(f"{r['customer_id']:<8} | {r['name']:<25} | {r['phone']:<15}")
    else:
        print(f"[INFO] No matching customer found for '{query}'.")

# --- Inventory Management Functions ---

def add_inventory_item():
    inventory = load_json('inventory.json')
    if inventory is None: return

    print("\n--- Add New Inventory Item ---")
    item_id = generate_id("I", inventory, "item_id")
    print(f"Generated Item ID: {item_id}")

    try:
        name = input("Enter Item Name: ").strip()
        if not name:
            print("[ERROR] Item name cannot be empty.")
            return
            
        category = input("Enter Category: ").strip()
        qty = int(input("Enter Total Quantity: "))
        if qty < 0:
            print("[ERROR] Quantity cannot be negative.")
            return

        rent_input = input("Enter Rent Per Day (₹): ")
        rent = Decimal(rent_input)

        new_item = {
            "item_id": item_id,
            "name": name,
            "category": category,
            "total_quantity": qty,
            "rent_per_day": rent
        }
        
        inventory.append(new_item)
        save_json('inventory.json', inventory)
        print(f"[SUCCESS] Item '{name}' added with ID: {item_id}")
        
    except ValueError:
        print("[ERROR] Invalid numeric input for Quantity.")
    except Exception as e:
        print(f"[ERROR] Invalid rent amount: {e}")

def view_inventory():
    inventory = load_json('inventory.json')
    if not inventory:
        if inventory is None: return
        print("\nInventory is empty.")
        return

    print("\n" + "="*80)
    print(f"{'ID':<8} | {'Item Name':<25} | {'Category':<15} | {'Qty':<5} | {'Rent':<10}")
    print("-" * 80)
    for item in inventory:
        print(f"{item['item_id']:<8} | {item['name']:<25} | {item['category']:<15} | {item['total_quantity']:<5} | ₹{item['rent_per_day']}")
    print("="*80)

def update_inventory_item():
    inventory = load_json('inventory.json')
    if not inventory:
        if inventory is None: return
        print("\nInventory is empty.")
        return
    
    search_id = input("\nEnter Item ID to update: ").strip().upper()
    found_item = next((item for item in inventory if item['item_id'] == search_id), None)
    
    if not found_item:
        print(f"[ERROR] Item ID '{search_id}' not found!")
        return

    print(f"\nUpdating '{found_item['name']}' ({search_id}). [Leave blank to skip]")
    
    name = input(f"New Name [{found_item['name']}]: ").strip()
    if name: found_item['name'] = name
    
    cat = input(f"New Category [{found_item['category']}]: ").strip()
    if cat: found_item['category'] = cat
    
    try:
        qty_in = input(f"New Quantity [{found_item['total_quantity']}]: ").strip()
        if qty_in: 
            q = int(qty_in)
            if q < 0: raise ValueError("Negative quantity")
            found_item['total_quantity'] = q
            
        rent_in = input(f"New Rent [{found_item['rent_per_day']}]: ").strip()
        if rent_in: found_item['rent_per_day'] = Decimal(rent_in)

        save_json('inventory.json', inventory)
        print("[SUCCESS] Item updated successfully!")
    except ValueError:
        print("[ERROR] Invalid numeric input. Change cancelled for that field.")
    except Exception as e:
        print(f"[ERROR] Update failed: {e}")

# --- Equipment Unit Management Functions ---

def add_equipment_unit():
    units = load_json('equipment_units.json')
    inventory = load_json('inventory.json')
    if units is None or inventory is None: return

    print("\n--- Add New Equipment Unit ---")
    unit_id = generate_id("U", units, "unit_id")
    print(f"Generated Unit ID: {unit_id}")
    
    item_id = input("Enter associated Item ID (e.g., I101): ").strip().upper()
    item_match = next((i for i in inventory if i['item_id'] == item_id), None)
    
    if not item_match:
        print(f"[ERROR] Item ID '{item_id}' does not exist in inventory.")
        return

    name = input(f"Enter Unit Name (Default: {item_match['name']}): ").strip() or item_match['name']
    status = input("Enter Status (Available/Maintenance/Broken) [Available]: ").strip() or "Available"

    new_unit = {
        "unit_id": unit_id,
        "item_id": item_id,
        "unit_name": name,
        "status": status
    }
    
    units.append(new_unit)
    save_json('equipment_units.json', units)
    print(f"[SUCCESS] Unit '{unit_id}' linked to '{item_id}' added!")

def view_equipment_units():
    units = load_json('equipment_units.json')
    if not units:
        if units is None: return
        print("\nNo equipment units recorded.")
        return

    print("\n" + "="*80)
    print(f"{'Unit ID':<10} | {'Item ID':<10} | {'Unit Name':<30} | {'Status':<15}")
    print("-" * 80)
    for u in units:
        print(f"{u['unit_id']:<10} | {u['item_id']:<10} | {u['unit_name']:<30} | {u['status']:<15}")
    print("="*80)

def change_unit_status():
    units = load_json('equipment_units.json')
    if not units:
        if units is None: return
        print("\nNo units recorded.")
        return

    uid = input("\nEnter Unit ID to change status (e.g., U101): ").strip().upper()
    unit = next((u for u in units if u['unit_id'] == uid), None)
            
    if unit:
        print(f"Current Status of {uid}: {unit['status']}")
        new_status = input("Enter new status (Available/Maintenance/Broken): ").strip()
        if new_status:
            unit['status'] = new_status
            save_json('equipment_units.json', units)
            print(f"[SUCCESS] Status for {uid} updated to {new_status}.")
        else:
            print("[INFO] No change made.")
    else:
        print(f"[ERROR] Unit ID '{uid}' not found.")

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
