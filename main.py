import json
import os
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

# --- Configuration & Constants ---
DATA_DIR = "data"
VALID_CATEGORIES = ["Tent", "Chair", "Table", "Lighting", "Catering", "Decoration", "Others"]
VALID_STATUSES = ["Available", "Maintenance", "Broken"]

def ensure_data_dir():
    """Ensures the data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

# --- File Operations ---

# --- Helper Functions ---

def load_json(filename):
    """Loads a JSON file from the data directory. Returns [] if not found, None if corrupted."""
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r') as file:
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
    """Saves data into a JSON file in the data directory. Returns True if successful."""
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4, cls=DecimalEncoder)
        return True
    except Exception as e:
        print(f"\n[ERROR] Could not save to '{filename}': {e}")
        return False

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

def get_validated_input(prompt, valid_options, allow_blank=False):
    """Prompts for input and validates it against a list of options."""
    options_str = "/".join(valid_options)
    while True:
        val = input(f"{prompt} ({options_str}){' [Leave blank to skip]' if allow_blank else ''}: ").strip()
        if not val and allow_blank:
            return None
        
        # Check for case-insensitive match
        match = next((opt for opt in valid_options if opt.lower() == val.lower()), None)
        if match:
            return match
        
        print(f"[ERROR] Invalid input. Please choose from: {options_str}")

def find_record_by_name_or_id(data, key_id, key_name):
    """Finds a record by ID or Name. Returns the record or None if not found or ambiguous."""
    query = input(f"\nEnter {key_name} or {key_id} to search: ").strip().lower()
    if not query:
        return None
        
    results = [r for r in data if query == str(r[key_id]).lower() or query in str(r[key_name]).lower()]
    
    if not results:
        print(f"[ERROR] No match found for '{query}'.")
        return None
    
    if len(results) > 1:
        print(f"\nMultiple matches found for '{query}':")
        for i, r in enumerate(results):
            print(f"{i+1}. {r[key_id]} - {r[key_name]}")
        
        try:
            choice = int(input(f"Select 1-{len(results)} (or 0 to cancel): "))
            if 0 < choice <= len(results):
                return results[choice-1]
            return None
        except ValueError:
            return None
            
    return results[0]

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
    if not phone.isdigit() or len(phone) != 10:
        print("[ERROR] Phone number must be exactly 10 digits.")
        return

    duplicate = next((c for c in customers if c['phone'] == phone), None)
    if duplicate:
        print(f"[ERROR] A customer with this phone number already exists: {duplicate['name']} (ID: {duplicate['customer_id']})")
        return

    address = input("Enter Address: ").strip()

    new_customer = {
        "customer_id": cust_id,
        "name": name,
        "phone": phone,
        "address": address
    }
    
    customers.append(new_customer)
    if save_json('customers.json', customers):
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

def delete_customer():
    customers = load_json('customers.json')
    if not customers:
        if customers is None: return
        print("\nNo customers to delete.")
        return

    print("\n--- Delete Customer ---")
    record = find_record_by_name_or_id(customers, "customer_id", "name")
    if not record: return

    confirm = input(f"Are you sure you want to delete '{record['name']}' ({record['customer_id']})? (y/n): ").lower()
    if confirm == 'y':
        # In Phase 1, there are no bookings to check yet. 
        # In later phases, we'd check if customer has active bookings.
        customers = [c for c in customers if c['customer_id'] != record['customer_id']]
        if save_json('customers.json', customers):
            print(f"[SUCCESS] Customer '{record['name']}' deleted.")
    else:
        print("[INFO] Deletion cancelled.")

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
            
        category = get_validated_input("Enter Category", VALID_CATEGORIES)
        qty = int(input("Enter Total Quantity: "))
        if qty < 0:
            print("[ERROR] Quantity cannot be negative.")
            return

        rent_input = input("Enter Rent Per Day (₹): ")
        rent = Decimal(rent_input)
        if rent <= 0:
            print("[ERROR] Rent per day must be a positive number.")
            return

        new_item = {
            "item_id": item_id,
            "name": name,
            "category": category,
            "total_quantity": qty,
            "rent_per_day": rent
        }
        
        inventory.append(new_item)
        if save_json('inventory.json', inventory):
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
    
    print("\n--- Update Inventory Item ---")
    found_item = find_record_by_name_or_id(inventory, "item_id", "name")
    
    if not found_item:
        return

    print(f"\nUpdating '{found_item['name']}' ({found_item['item_id']}). [Leave blank to skip]")
    
    name = input(f"New Name [{found_item['name']}]: ").strip()
    if name: found_item['name'] = name
    
    cat = get_validated_input("New Category", VALID_CATEGORIES, allow_blank=True)
    if cat: found_item['category'] = cat
    
    try:
        qty_in = input(f"New Quantity [{found_item['total_quantity']}]: ").strip()
        if qty_in: 
            q = int(qty_in)
            if q < 0: raise ValueError("Negative quantity")
            found_item['total_quantity'] = q
            
        rent_in = input(f"New Rent [{found_item['rent_per_day']}]: ").strip()
        if rent_in:
            r = Decimal(rent_in)
            if r <= 0:
                print("[ERROR] Rent per day must be a positive number.")
                return
            found_item['rent_per_day'] = r

        if save_json('inventory.json', inventory):
            print("[SUCCESS] Item updated successfully!")
    except ValueError:
        print("[ERROR] Invalid numeric input. Change cancelled for that field.")
    except Exception as e:
        print(f"[ERROR] Update failed: {e}")

def delete_inventory_item():
    inventory = load_json('inventory.json')
    units = load_json('equipment_units.json')
    if not inventory:
        if inventory is None: return
        print("\nInventory is empty.")
        return

    print("\n--- Delete Inventory Item ---")
    item = find_record_by_name_or_id(inventory, "item_id", "name")
    if not item: return

    # Reference check: cannot delete if units are linked
    linked_units = [u for u in units if u['item_id'] == item['item_id']]
    if linked_units:
        print(f"[ERROR] Cannot delete '{item['name']}' because it has {len(linked_units)} linked equipment units.")
        return

    confirm = input(f"Are you sure you want to delete '{item['name']}'? (y/n): ").lower()
    if confirm == 'y':
        inventory = [i for i in inventory if i['item_id'] != item['item_id']]
        if save_json('inventory.json', inventory):
            print(f"[SUCCESS] Item '{item['name']}' deleted.")
    else:
        print("[INFO] Deletion cancelled.")

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
    status = get_validated_input("Enter Status", VALID_STATUSES, allow_blank=True) or "Available"

    new_unit = {
        "unit_id": unit_id,
        "item_id": item_id,
        "unit_name": name,
        "status": status
    }
    
    units.append(new_unit)
    if save_json('equipment_units.json', units):
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

    print("\n--- Change Equipment Unit Status ---")
    unit = find_record_by_name_or_id(units, "unit_id", "unit_name")
    if not unit:
        return
            
    print(f"Current Status of {unit['unit_id']}: {unit['status']}")
    new_status = get_validated_input("Enter new status", VALID_STATUSES, allow_blank=True)
    if new_status:
        unit['status'] = new_status
        if save_json('equipment_units.json', units):
            print(f"[SUCCESS] Status for {unit['unit_id']} updated to {new_status}.")
    else:
        print("[INFO] No change made.")

def delete_equipment_unit():
    units = load_json('equipment_units.json')
    if not units:
        if units is None: return
        print("\nNo units recorded.")
        return

    print("\n--- Delete Equipment Unit ---")
    unit = find_record_by_name_or_id(units, "unit_id", "unit_name")
    if not unit: return

    confirm = input(f"Are you sure you want to delete Unit '{unit['unit_id']}' ({unit['unit_name']})? (y/n): ").lower()
    if confirm == 'y':
        units = [u for u in units if u['unit_id'] != unit['unit_id']]
        if save_json('equipment_units.json', units):
            print(f"[SUCCESS] Equipment unit '{unit['unit_id']}' deleted.")
    else:
        print("[INFO] Deletion cancelled.")

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
        print("4. Delete Customer")
        print("5. Back to Main Menu")
        
        choice = input("Select an Option: ")
        
        if choice == '1': add_customer()
        elif choice == '2': view_customers()
        elif choice == '3': search_customer()
        elif choice == '4': delete_customer()
        elif choice == '5': break
        else: print("Invalid selection.")

def inventory_menu():
    while True:
        print("\n--- Inventory Management ---")
        print("1. Add Item to Inventory")
        print("2. View Inventory List")
        print("3. Update Item Details")
        print("4. Delete Inventory Item")
        print("5. Back to Main Menu")
        
        choice = input("Select an Option: ")
        
        if choice == '1': add_inventory_item()
        elif choice == '2': view_inventory()
        elif choice == '3': update_inventory_item()
        elif choice == '4': delete_inventory_item()
        elif choice == '5': break
        else: print("Invalid selection.")

def equipment_menu():
    while True:
        print("\n--- Equipment Unit Management ---")
        print("1. Add Equipment Unit")
        print("2. View Unit Status")
        print("3. Change Unit Status")
        print("4. Delete Equipment Unit")
        print("5. Back to Main Menu")
        
        choice = input("Select an Option: ")
        
        if choice == '1': add_equipment_unit()
        elif choice == '2': view_equipment_units()
        elif choice == '3': change_unit_status()
        elif choice == '4': delete_equipment_unit()
        elif choice == '5': break
        else: print("Invalid selection.")

if __name__ == "__main__":
    main_menu()
