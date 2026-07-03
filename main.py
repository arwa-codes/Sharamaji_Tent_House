import json
import os
from decimal import Decimal
from datetime import datetime, timedelta
import calendar

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
            elif "bookings.json" in filename:
                for b in data:
                    b['total_amount'] = Decimal(b.get('total_amount', 0))
                    b['deposit_paid'] = Decimal(b.get('deposit_paid', 0))
                    b['remaining_amount'] = Decimal(b.get('remaining_amount', 0))
                    b['discount'] = Decimal(b.get('discount', 0))
            elif "booking_items.json" in filename:
                for bi in data:
                    bi['price_per_day'] = Decimal(bi.get('price_per_day', 0))
                    bi['total'] = Decimal(bi.get('total', 0))
            elif "payments.json" in filename:
                for p in data:
                    p['payment_amount'] = Decimal(p.get('payment_amount', 0))
            elif "returns.json" in filename:
                for r in data:
                    r['returned_quantity'] = int(r.get('returned_quantity', 0))
                    r['damaged_quantity'] = int(r.get('damaged_quantity', 0))
                    r['missing_quantity'] = int(r.get('missing_quantity', 0))
                    r['late_charges'] = Decimal(r.get('late_charges', 0))
                    r['extra_charges'] = Decimal(r.get('extra_charges', 0))
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

def parse_date(date_str):
    """Parses a date string (YYYY-MM-DD) into a datetime.date object. Returns None if invalid."""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None

def calculate_item_availability(item_id, start_date_str, end_date_str, exclude_booking_id=None):
    """Calculates available quantity of an item within a date range, taking active bookings and broken/maintenance units into account."""
    inventory = load_json('inventory.json')
    item = next((i for i in inventory if i['item_id'] == item_id), None)
    if not item:
        return 0
        
    # Subtract maintenance or broken units from total quantity to get effective stock
    units = load_json('equipment_units.json')
    total_unavailable = len([u for u in units if u['item_id'] == item_id and u['status'] in ['Maintenance', 'Broken']])
    total_stock = max(0, item['total_quantity'] - total_unavailable)
    
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    if not start_date or not end_date or start_date > end_date:
        return 0
        
    bookings = load_json('bookings.json')
    booking_items = load_json('booking_items.json')
    
    # Identify active (not cancelled) bookings that overlap with the proposed range:
    # Overlap condition: b_start <= end_date and b_end >= start_date
    overlapping_booking_ids = set()
    for b in bookings:
        if b.get('status') == 'Cancelled':
            continue
        if b['booking_id'] == exclude_booking_id:
            continue
        
        b_start = parse_date(b['delivery_date'])
        b_end = parse_date(b['return_date'])
        if b_start and b_end:
            if b_start <= end_date and b_end >= start_date:
                overlapping_booking_ids.add(b['booking_id'])
                
    # Group booking items by booking_id
    items_by_booking = {}
    for bi in booking_items:
        if bi['item_id'] == item_id and bi['booking_id'] in overlapping_booking_ids:
            items_by_booking[bi['booking_id']] = items_by_booking.get(bi['booking_id'], 0) + int(bi['quantity'])
            
    # Calculate the quantity booked on each single day in the proposed range [start_date, end_date]
    curr_date = start_date
    max_booked = 0
    while curr_date <= end_date:
        booked_today = 0
        for b in bookings:
            if b['booking_id'] in items_by_booking:
                b_start = parse_date(b['delivery_date'])
                b_end = parse_date(b['return_date'])
                if b_start <= curr_date <= b_end:
                    booked_today += items_by_booking[b['booking_id']]
        if booked_today > max_booked:
            max_booked = booked_today
        curr_date += timedelta(days=1)
        
    return max(0, total_stock - max_booked)

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
        bookings = load_json('bookings.json')
        linked_bookings = [b for b in bookings if b['customer_id'] == record['customer_id'] and b.get('status') != 'Cancelled']
        if linked_bookings:
            print(f"[ERROR] Cannot delete customer '{record['name']}' because they have {len(linked_bookings)} active booking(s).")
            return
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

        rent_input = input("Enter Rent Per Day (Rs.): ")
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
        print(f"{item['item_id']:<8} | {item['name']:<25} | {item['category']:<15} | {item['total_quantity']:<5} | Rs.{item['rent_per_day']}")
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

    booking_items = load_json('booking_items.json')
    bookings = load_json('bookings.json')
    active_booking_ids = [b['booking_id'] for b in bookings if b.get('status') != 'Cancelled']
    linked_bookings = [bi for bi in booking_items if bi['item_id'] == item['item_id'] and bi['booking_id'] in active_booking_ids]
    if linked_bookings:
        print(f"[ERROR] Cannot delete '{item['name']}' because it is linked to {len(linked_bookings)} active booking(s).")
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

# --- Booking Management Functions ---

def show_conflicting_bookings(item_id, start_date, end_date):
    bookings = load_json('bookings.json')
    booking_items = load_json('booking_items.json')
    customers = load_json('customers.json')
    
    print("\n--- Conflicting Bookings ---")
    print(f"{'Booking ID':<12} | {'Customer':<20} | {'Delivery':<12} | {'Return':<12} | {'Qty Booked':<10}")
    print("-" * 75)
    count = 0
    for b in bookings:
        if b.get('status') == 'Cancelled':
            continue
        b_start = parse_date(b['delivery_date'])
        b_end = parse_date(b['return_date'])
        if b_start and b_end and b_start <= end_date and b_end >= start_date:
            qty = sum(int(bi['quantity']) for bi in booking_items if bi['booking_id'] == b['booking_id'] and bi['item_id'] == item_id)
            if qty > 0:
                cust = next((c for c in customers if c['customer_id'] == b['customer_id']), None)
                cust_name = cust['name'] if cust else "Unknown"
                print(f"{b['booking_id']:<12} | {cust_name:<20} | {b['delivery_date']:<12} | {b['return_date']:<12} | {qty:<10}")
                count += 1
    if count == 0:
        print("No conflicting bookings found (deficit could be due to broken/maintenance units).")

def create_booking():
    customers = load_json('customers.json')
    inventory = load_json('inventory.json')
    bookings = load_json('bookings.json')
    booking_items = load_json('booking_items.json')
    
    if customers is None or inventory is None or bookings is None or booking_items is None:
        return
        
    print("\n--- Create New Booking ---")
    
    customer = find_record_by_name_or_id(customers, "customer_id", "name")
    if not customer:
        print("[ERROR] Customer selection is required to create a booking.")
        return
        
    event_type = input("Enter Event Type (e.g., Wedding, Birthday): ").strip()
    event_location = input("Enter Event Location: ").strip()
    
    while True:
        del_date_str = input("Enter Delivery Date (YYYY-MM-DD): ").strip()
        del_date = parse_date(del_date_str)
        if del_date:
            break
        print("[ERROR] Invalid date format. Please use YYYY-MM-DD.")
        
    while True:
        ret_date_str = input("Enter Return Date (YYYY-MM-DD): ").strip()
        ret_date = parse_date(ret_date_str)
        if not ret_date:
            print("[ERROR] Invalid date format. Please use YYYY-MM-DD.")
            continue
        if ret_date < del_date:
            print("[ERROR] Return date cannot be before delivery date.")
            continue
        break
        
    total_days = max(1, (ret_date - del_date).days)
    print(f"Total Rental Duration: {total_days} day(s)")
    
    temp_items = {}
    print("\n--- Add Items to Booking (Press Enter with empty query to finish) ---")
    while True:
        item = find_record_by_name_or_id(inventory, "item_id", "name")
        if not item:
            break
            
        qty_str = input(f"Enter Quantity for '{item['name']}': ").strip()
        if not qty_str:
            print("[INFO] Item skipped.")
            continue
            
        try:
            qty = int(qty_str)
            if qty <= 0:
                print("[ERROR] Quantity must be positive.")
                continue
        except ValueError:
            print("[ERROR] Invalid quantity.")
            continue
            
        current_added = temp_items.get(item['item_id'], 0)
        proposed_qty = current_added + qty
        
        available = calculate_item_availability(item['item_id'], del_date_str, ret_date_str)
        if proposed_qty > available:
            print(f"[ERROR] Cannot book {proposed_qty} units of '{item['name']}'. Only {available} units are available during this period.")
            show_conflicting_bookings(item['item_id'], del_date, ret_date)
            continue
            
        temp_items[item['item_id']] = proposed_qty
        print(f"[SUCCESS] Added {qty} x '{item['name']}' to current booking list (Total: {proposed_qty}).")
        
    if not temp_items:
        print("[ERROR] No items added to booking. Booking cancelled.")
        return
        
    total_amount = Decimal(0)
    for item_id, qty in temp_items.items():
        item_match = next(i for i in inventory if i['item_id'] == item_id)
        total_amount += item_match['rent_per_day'] * qty * total_days
        
    print(f"\nInitial Subtotal Amount: Rs.{total_amount}")
    
    discount = Decimal(0)
    discount_str = input("Enter Discount (Rs.) [0]: ").strip() or "0"
    try:
        discount = Decimal(discount_str)
        if discount < 0:
            print("[ERROR] Discount cannot be negative. Set to 0.")
            discount = Decimal(0)
    except:
        print("[ERROR] Invalid numeric discount. Set to 0.")
        discount = Decimal(0)
        
    deposit = Decimal(0)
    deposit_str = input("Enter Deposit Paid (Rs.) [0]: ").strip() or "0"
    try:
        deposit = Decimal(deposit_str)
        if deposit < 0:
            print("[ERROR] Deposit cannot be negative. Set to 0.")
            deposit = Decimal(0)
    except:
        print("[ERROR] Invalid numeric deposit. Set to 0.")
        deposit = Decimal(0)
        
    if discount + deposit > total_amount:
        print("[ERROR] Discount + Deposit cannot exceed subtotal amount. Booking cancelled.")
        return
        
    remaining = total_amount - discount - deposit
    
    booking_id = generate_id("B", bookings, "booking_id")
    booking_date = datetime.now().strftime("%Y-%m-%d")
    
    new_booking = {
        "booking_id": booking_id,
        "customer_id": customer['customer_id'],
        "event_type": event_type,
        "event_location": event_location,
        "booking_date": booking_date,
        "delivery_date": del_date_str,
        "return_date": ret_date_str,
        "total_amount": total_amount,
        "deposit_paid": deposit,
        "remaining_amount": remaining,
        "discount": discount,
        "status": "Confirmed"
    }
    
    new_items_list = []
    for item_id, qty in temp_items.items():
        item_match = next(i for i in inventory if i['item_id'] == item_id)
        bi_id = generate_id("BI", booking_items + new_items_list, "booking_item_id")
        bi_total = item_match['rent_per_day'] * qty * total_days
        new_bi = {
            "booking_item_id": bi_id,
            "booking_id": booking_id,
            "item_id": item_id,
            "quantity": qty,
            "price_per_day": item_match['rent_per_day'],
            "total_days": total_days,
            "total": bi_total
        }
        new_items_list.append(new_bi)
        
    bookings.append(new_booking)
    booking_items.extend(new_items_list)
    
    if save_json('bookings.json', bookings) and save_json('booking_items.json', booking_items):
        print(f"\n[SUCCESS] Booking '{booking_id}' created successfully for customer '{customer['name']}'!")
        print(f"Total Amount: Rs.{total_amount} | Discount: Rs.{discount} | Deposit Paid: Rs.{deposit} | Remaining: Rs.{remaining}")
    else:
        print("[ERROR] Failed to save booking data.")

def view_bookings():
    bookings = load_json('bookings.json')
    customers = load_json('customers.json')
    if not bookings:
        if bookings is None: return
        print("\nNo bookings found.")
        return
        
    print("\n" + "="*115)
    print(f"{'ID':<8} | {'Customer Name':<25} | {'Delivery':<12} | {'Return':<12} | {'Total':<10} | {'Paid':<10} | {'Remaining':<10} | {'Status':<10}")
    print("-" * 115)
    for b in bookings:
        cust = next((c for c in customers if c['customer_id'] == b['customer_id']), None)
        cust_name = cust['name'] if cust else "Unknown"
        print(f"{b['booking_id']:<8} | {cust_name:<25} | {b['delivery_date']:<12} | {b['return_date']:<12} | Rs.{b['total_amount']:<9} | Rs.{b['deposit_paid']:<9} | Rs.{b['remaining_amount']:<9} | {b['status']:<10}")
    print("="*115)

def view_booking_details():
    bookings = load_json('bookings.json')
    customers = load_json('customers.json')
    booking_items = load_json('booking_items.json')
    inventory = load_json('inventory.json')
    
    if not bookings:
        if bookings is None: return
        print("\nNo bookings found.")
        return
        
    print("\n--- Search and View Booking Details ---")
    booking = find_record_by_name_or_id(bookings, "booking_id", "delivery_date")
    if not booking:
        query = input("Enter Customer Name to search bookings: ").strip().lower()
        if not query:
            return
        matching_custs = [c['customer_id'] for c in customers if query in c['name'].lower()]
        matching_bookings = [b for b in bookings if b['customer_id'] in matching_custs]
        if not matching_bookings:
            print("[ERROR] No bookings found for that customer name.")
            return
        if len(matching_bookings) > 1:
            print("\nMultiple bookings found:")
            for idx, mb in enumerate(matching_bookings):
                cust = next(c for c in customers if c['customer_id'] == mb['customer_id'])
                print(f"{idx+1}. {mb['booking_id']} - {cust['name']} ({mb['delivery_date']} to {mb['return_date']})")
            try:
                choice = int(input(f"Select 1-{len(matching_bookings)} (or 0 to cancel): "))
                if 0 < choice <= len(matching_bookings):
                    booking = matching_bookings[choice-1]
                else:
                    return
            except ValueError:
                return
        else:
            booking = matching_bookings[0]
            
    cust = next((c for c in customers if c['customer_id'] == booking['customer_id']), None)
    print("\n==========================================================================")
    print(f" BOOKING DETAILS - {booking['booking_id']} ({booking['status']})")
    print("==========================================================================")
    if cust:
        print(f"Customer Name : {cust['name']}")
        print(f"Phone Number  : {cust['phone']}")
        print(f"Address       : {cust['address']}")
    else:
        print("Customer Name : Unknown Customer")
    print("-" * 74)
    print(f"Event Type    : {booking.get('event_type', 'N/A')}")
    print(f"Location      : {booking.get('event_location', 'N/A')}")
    print(f"Booking Date  : {booking.get('booking_date', 'N/A')}")
    print(f"Delivery Date : {booking['delivery_date']}")
    print(f"Return Date   : {booking['return_date']}")
    print("-" * 74)
    
    items_in_booking = [bi for bi in booking_items if bi['booking_id'] == booking['booking_id']]
    print(f"{'Item ID':<8} | {'Item Name':<25} | {'Quantity':<8} | {'Rate':<8} | {'Days':<5} | {'Total':<10}")
    print("-" * 74)
    for bi in items_in_booking:
        inv_item = next((i for i in inventory if i['item_id'] == bi['item_id']), None)
        item_name = inv_item['name'] if inv_item else "Unknown Item"
        print(f"{bi['item_id']:<8} | {item_name:<25} | {bi['quantity']:<8} | Rs.{bi['price_per_day']:<7} | {bi['total_days']:<5} | Rs.{bi['total']:<9}")
    print("-" * 74)
    print(f"{'Subtotal Amount:':<52} Rs.{booking['total_amount']}")
    print(f"{'Discount:':<52} Rs.{booking['discount']}")
    print(f"{'Deposit Paid:':<52} Rs.{booking['deposit_paid']}")
    print(f"{'Remaining Balance:':<52} Rs.{booking['remaining_amount']}")
    print("==========================================================================")

def cancel_booking():
    bookings = load_json('bookings.json')
    customers = load_json('customers.json')
    if not bookings:
        if bookings is None: return
        print("\nNo bookings found.")
        return
        
    print("\n--- Cancel Booking ---")
    booking = find_record_by_name_or_id(bookings, "booking_id", "delivery_date")
    if not booking:
        return
        
    if booking['status'] == 'Cancelled':
        print("[INFO] This booking is already cancelled.")
        return
        
    cust = next((c for c in customers if c['customer_id'] == booking['customer_id']), None)
    cust_name = cust['name'] if cust else "Unknown"
    
    confirm = input(f"Are you sure you want to cancel booking '{booking['booking_id']}' for '{cust_name}'? (y/n): ").lower()
    if confirm == 'y':
        booking['status'] = 'Cancelled'
        if save_json('bookings.json', bookings):
            print(f"[SUCCESS] Booking '{booking['booking_id']}' has been cancelled.")
    else:
        print("[INFO] Cancellation cancelled.")

def record_payment():
    bookings = load_json('bookings.json')
    if not bookings:
        if bookings is None: return
        print("\nNo bookings found.")
        return
        
    print("\n--- Record Payment ---")
    booking = find_record_by_name_or_id(bookings, "booking_id", "delivery_date")
    if not booking:
        return
        
    if booking['status'] == 'Cancelled':
        print("[ERROR] Cannot record payment for a cancelled booking.")
        return
        
    payments = load_json('payments.json')
    if payments is None:
        return
        
    print(f"\nBooking ID: {booking['booking_id']}")
    print(f"Total Rental Amount: Rs.{booking['total_amount']}")
    print(f"Discount Applied: Rs.{booking['discount']}")
    print(f"Deposit Paid: Rs.{booking['deposit_paid']}")
    
    # Calculate total payments made already
    booking_payments = [p for p in payments if p['booking_id'] == booking['booking_id']]
    total_paid_after_deposit = sum(Decimal(p['payment_amount']) for p in booking_payments)
    
    current_remaining = booking['remaining_amount']
    print(f"Total Payments Made: Rs.{total_paid_after_deposit}")
    print(f"Current Remaining Balance: Rs.{current_remaining}")
    
    if current_remaining <= 0:
        print("[INFO] This booking is already fully paid.")
        return
        
    print("\nSelect Payment Type:")
    print("1. Full Payment")
    print("2. Partial Payment")
    choice = input("Select Option (1-2): ").strip()
    
    if choice == '1':
        payment_amount = current_remaining
        print(f"Selected Full Payment: Rs.{payment_amount}")
    elif choice == '2':
        amount_str = input("Enter Payment Amount (Rs.): ").strip()
        try:
            payment_amount = Decimal(amount_str)
            if payment_amount <= 0:
                print("[ERROR] Payment amount must be a positive number.")
                return
            if payment_amount > current_remaining:
                print(f"[ERROR] Payment amount greater than remaining balance (Rs.{current_remaining}).")
                return
        except Exception as e:
            print(f"[ERROR] Invalid numeric amount: {e}")
            return
    else:
        print("[ERROR] Invalid choice. Payment cancelled.")
        return
        
    payment_id = generate_id("P", payments, "payment_id")
    payment_date = datetime.now().strftime("%Y-%m-%d")
    
    new_payment = {
        "payment_id": payment_id,
        "booking_id": booking['booking_id'],
        "payment_amount": payment_amount,
        "payment_date": payment_date
    }
    
    payments.append(new_payment)
    booking['remaining_amount'] = current_remaining - payment_amount
    
    if save_json('payments.json', payments) and save_json('bookings.json', bookings):
        print(f"\n[SUCCESS] Payment of Rs.{payment_amount} recorded successfully!")
        print(f"New Remaining Balance: Rs.{booking['remaining_amount']}")
    else:
        print("[ERROR] Failed to save payment record.")

def apply_discount_to_booking():
    bookings = load_json('bookings.json')
    if not bookings:
        if bookings is None: return
        print("\nNo bookings found.")
        return
        
    print("\n--- Apply Discount ---")
    booking = find_record_by_name_or_id(bookings, "booking_id", "delivery_date")
    if not booking:
        return
        
    if booking['status'] == 'Cancelled':
        print("[ERROR] Cannot apply discount to a cancelled booking.")
        return
    if booking['status'] == 'Closed':
        print("[ERROR] Cannot apply discount to a closed booking.")
        return
        
    print(f"\nBooking ID: {booking['booking_id']}")
    print(f"Total Amount: Rs.{booking['total_amount']}")
    print(f"Current Discount Applied: Rs.{booking['discount']}")
    print(f"Current Remaining Balance: Rs.{booking['remaining_amount']}")
    
    discount_str = input("Enter Additional Discount Amount (Rs.): ").strip()
    try:
        additional_discount = Decimal(discount_str)
        if additional_discount <= 0:
            print("[ERROR] Discount amount must be positive.")
            return
        if additional_discount > booking['remaining_amount']:
            print("[ERROR] Additional discount cannot exceed the remaining balance.")
            return
    except Exception as e:
        print(f"[ERROR] Invalid numeric amount: {e}")
        return
        
    booking['discount'] += additional_discount
    booking['remaining_amount'] -= additional_discount
    
    if save_json('bookings.json', bookings):
        print(f"\n[SUCCESS] Additional discount of Rs.{additional_discount} applied successfully!")
        print(f"New Total Discount: Rs.{booking['discount']}")
        print(f"New Remaining Balance: Rs.{booking['remaining_amount']}")
    else:
        print("[ERROR] Failed to save booking details.")

def record_return():
    bookings = load_json('bookings.json')
    if not bookings:
        if bookings is None: return
        print("\nNo bookings found.")
        return
        
    print("\n--- Record Return & Damage ---")
    booking = find_record_by_name_or_id(bookings, "booking_id", "delivery_date")
    if not booking:
        return
        
    if booking['status'] == 'Cancelled':
        print("[ERROR] Cannot record returns for a cancelled booking.")
        return
    if booking['status'] == 'Closed':
        print("[ERROR] This booking is already closed.")
        return
        
    booking_items = load_json('booking_items.json')
    inventory = load_json('inventory.json')
    returns = load_json('returns.json')
    
    if booking_items is None or inventory is None or returns is None:
        return
        
    items_in_booking = [bi for bi in booking_items if bi['booking_id'] == booking['booking_id']]
    if not items_in_booking:
        print("[ERROR] No items found in this booking.")
        return
        
    print(f"\nItems in Booking '{booking['booking_id']}':")
    
    returns_added = []
    any_return_recorded = False
    
    for bi in items_in_booking:
        item_id = bi['item_id']
        inv_item = next((i for i in inventory if i['item_id'] == item_id), None)
        item_name = inv_item['name'] if inv_item else "Unknown Item"
        
        item_returns = [r for r in returns if r['booking_id'] == booking['booking_id'] and r['item_id'] == item_id]
        already_returned = sum(r['returned_quantity'] for r in item_returns)
        already_damaged = sum(r['damaged_quantity'] for r in item_returns)
        already_missing = sum(r['missing_quantity'] for r in item_returns)
        
        total_accounted = already_returned + already_damaged + already_missing
        booked_qty = int(bi['quantity'])
        remaining_qty = booked_qty - total_accounted
        
        print(f"\nItem: {item_name} ({item_id})")
        print(f"  Booked Quantity     : {booked_qty}")
        print(f"  Already Returned    : {already_returned}")
        print(f"  Already Damaged     : {already_damaged}")
        print(f"  Already Missing     : {already_missing}")
        print(f"  Remaining to Account: {remaining_qty}")
        
        if remaining_qty <= 0:
            print("  [INFO] All quantities of this item are already fully accounted for.")
            continue
            
        print(f"Enter return details for '{item_name}' (Press Enter with empty to skip this item):")
        ret_qty_str = input("  Quantity Returned in Good Condition: ").strip()
        if not ret_qty_str:
            print("  [INFO] Skipped return record for this item.")
            continue
            
        dmg_qty_str = input("  Quantity Damaged: ").strip() or "0"
        mis_qty_str = input("  Quantity Missing: ").strip() or "0"
        
        try:
            ret_qty = int(ret_qty_str)
            dmg_qty = int(dmg_qty_str)
            mis_qty = int(mis_qty_str)
            
            if ret_qty < 0 or dmg_qty < 0 or mis_qty < 0:
                print("  [ERROR] Quantities cannot be negative.")
                continue
                
            total_input = ret_qty + dmg_qty + mis_qty
            if total_input <= 0:
                print("  [ERROR] Total quantity entered must be greater than zero.")
                continue
                
            if total_input > remaining_qty:
                print(f"  [ERROR] Return quantity greater than issued quantity. (Remaining to account: {remaining_qty})")
                continue
        except ValueError:
            print("  [ERROR] Invalid numeric input. Item skipped.")
            continue
            
        late_charges_str = input("  Enter Late Charges (Rs.) [0]: ").strip() or "0"
        extra_charges_str = input("  Enter Extra Charges (Rs.) [0]: ").strip() or "0"
        
        try:
            late_charges = Decimal(late_charges_str)
            extra_charges = Decimal(extra_charges_str)
            if late_charges < 0 or extra_charges < 0:
                print("  [ERROR] Charges cannot be negative.")
                continue
        except Exception as e:
            print(f"  [ERROR] Invalid charges: {e}. Item skipped.")
            continue
            
        return_id = generate_id("R", returns + returns_added, "return_id")
        new_return = {
            "return_id": return_id,
            "booking_id": booking['booking_id'],
            "item_id": item_id,
            "returned_quantity": ret_qty,
            "damaged_quantity": dmg_qty,
            "missing_quantity": mis_qty,
            "late_charges": late_charges,
            "extra_charges": extra_charges
        }
        
        returns_added.append(new_return)
        any_return_recorded = True
        print(f"  [SUCCESS] Return record '{return_id}' prepared for '{item_name}' (Returned: {ret_qty}, Damaged: {dmg_qty}, Missing: {mis_qty})")
        
        if dmg_qty > 0:
            units = load_json('equipment_units.json')
            if units:
                avail_units = [u for u in units if u['item_id'] == item_id and u['status'] == 'Available']
                if avail_units:
                    print(f"\n  Found {len(avail_units)} 'Available' equipment units for '{item_name}'.")
                    print(f"  You reported {dmg_qty} damaged unit(s). Would you like to mark specific unit(s) as Broken/Maintenance now?")
                    u_choice = input("  Enter 'y' to choose specific units, or press Enter to skip unit updates: ").strip().lower()
                    if u_choice == 'y':
                        marked_count = 0
                        for u_idx, u in enumerate(avail_units):
                            if marked_count >= dmg_qty:
                                break
                            print(f"  {u_idx+1}. Unit ID: {u['unit_id']} | Name: {u['unit_name']}")
                        
                        to_update_ids = []
                        while len(to_update_ids) < dmg_qty:
                            u_sel = input(f"  Select unit to mark (1-{len(avail_units)}) or enter 0 to stop: ").strip()
                            if u_sel == '0' or not u_sel:
                                break
                            try:
                                sel_idx = int(u_sel) - 1
                                if 0 <= sel_idx < len(avail_units):
                                    selected_unit = avail_units[sel_idx]
                                    if selected_unit['unit_id'] in to_update_ids:
                                        print("  Unit already selected.")
                                        continue
                                    to_update_ids.append(selected_unit['unit_id'])
                                else:
                                    print("  Invalid selection.")
                            except ValueError:
                                print("  Please enter a number.")
                                
                        if to_update_ids:
                            new_status = get_validated_input("  Set status for selected unit(s)", ["Maintenance", "Broken"])
                            for u in units:
                                if u['unit_id'] in to_update_ids:
                                    u['status'] = new_status
                            save_json('equipment_units.json', units)
                            print(f"  [SUCCESS] Updated status of {len(to_update_ids)} unit(s) to '{new_status}'.")
                            
    if any_return_recorded:
        returns.extend(returns_added)
        total_additional_charges = sum(r['late_charges'] + r['extra_charges'] for r in returns_added)
        booking['remaining_amount'] += total_additional_charges
        
        if save_json('returns.json', returns) and save_json('bookings.json', bookings):
            print(f"\n[SUCCESS] {len(returns_added)} return record(s) saved successfully!")
            print(f"Total late/extra charges added: Rs.{total_additional_charges}")
            print(f"Updated Booking Remaining Balance: Rs.{booking['remaining_amount']}")
        else:
            print("[ERROR] Failed to save returns or booking details.")
    else:
        print("\n[INFO] No return records were created.")

def close_booking():
    bookings = load_json('bookings.json')
    if not bookings:
        if bookings is None: return
        print("\nNo bookings found.")
        return
        
    print("\n--- Close Booking ---")
    booking = find_record_by_name_or_id(bookings, "booking_id", "delivery_date")
    if not booking:
        return
        
    if booking['status'] == 'Cancelled':
        print("[ERROR] Cannot close a cancelled booking.")
        return
    if booking['status'] == 'Closed':
        print("[INFO] Booking is already closed.")
        return
        
    booking_items = load_json('booking_items.json')
    returns = load_json('returns.json')
    
    if booking_items is None or returns is None:
        return
        
    items_in_booking = [bi for bi in booking_items if bi['booking_id'] == booking['booking_id']]
    if not items_in_booking:
        print("[ERROR] No items found in this booking. Booking can be cancelled but not closed normally.")
        return
        
    all_accounted = True
    any_missing = False
    total_missing_count = 0
    unreturned_items = []
    
    for bi in items_in_booking:
        item_id = bi['item_id']
        item_returns = [r for r in returns if r['booking_id'] == booking['booking_id'] and r['item_id'] == item_id]
        
        already_returned = sum(r['returned_quantity'] for r in item_returns)
        already_damaged = sum(r['damaged_quantity'] for r in item_returns)
        already_missing = sum(r['missing_quantity'] for r in item_returns)
        
        total_accounted = already_returned + already_damaged + already_missing
        booked_qty = int(bi['quantity'])
        
        if total_accounted < booked_qty:
            all_accounted = False
            unreturned_items.append((item_id, booked_qty - total_accounted))
            
        if already_missing > 0:
            any_missing = True
            total_missing_count += already_missing
            
    if not all_accounted:
        print("\n[ERROR] Prevent closing booking if items are missing / unreturned.")
        print("The following items have not been fully returned or accounted for:")
        for item_id, unret_qty in unreturned_items:
            print(f"  - Item ID {item_id}: {unret_qty} unit(s) still outstanding.")
        return
        
    if any_missing:
        print(f"\n[ERROR] Prevent closing booking if items are missing.")
        print(f"There are {total_missing_count} item(s) marked as MISSING in the return records for this booking.")
        print("Missing items must be returned or resolved (e.g. replaced or paid for) before closing the booking.")
        return
        
    if booking['remaining_amount'] > 0:
        print(f"\n[WARNING] This booking has an outstanding balance of Rs.{booking['remaining_amount']}.")
        confirm_close = input("Would you still like to close it? (y/n): ").strip().lower()
        if confirm_close != 'y':
            print("[INFO] Closing cancelled.")
            return
    else:
        confirm_close = input(f"Are you sure you want to close booking '{booking['booking_id']}'? (y/n): ").strip().lower()
        if confirm_close != 'y':
            print("[INFO] Closing cancelled.")
            return
            
    booking['status'] = 'Closed'
    if save_json('bookings.json', bookings):
        print(f"\n[SUCCESS] Booking '{booking['booking_id']}' has been marked as CLOSED.")
    else:
        print("[ERROR] Failed to update booking status.")

def payments_returns_menu():
    while True:
        print("\n--- Payments, Returns & Damage Tracking ---")
        print("1. Record Payment (Full/Partial)")
        print("2. Apply Discount to Booking")
        print("3. Record Return & Damage")
        print("4. Close Booking")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect an Option (1-5): ")
        if choice == '1': record_payment()
        elif choice == '2': apply_discount_to_booking()
        elif choice == '3': record_return()
        elif choice == '4': close_booking()
        elif choice == '5': break
        else: print("Invalid choice, please select 1-5.")

def booking_menu():
    while True:
        print("\n--- Booking Management ---")
        print("1. Create New Booking")
        print("2. View All Bookings")
        print("3. View Booking Details")
        print("4. Cancel Booking")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect an Option (1-5): ")
        if choice == '1': create_booking()
        elif choice == '2': view_bookings()
        elif choice == '3': view_booking_details()
        elif choice == '4': cancel_booking()
        elif choice == '5': break
        else: print("Invalid choice, please select 1-5.")

def check_item_availability_cli():
    inventory = load_json('inventory.json')
    if not inventory:
        if inventory is None: return
        print("\nInventory is empty.")
        return
        
    print("\n--- Check Item Availability ---")
    item = find_record_by_name_or_id(inventory, "item_id", "name")
    if not item:
        return
        
    while True:
        start_str = input("Enter Start Date (YYYY-MM-DD): ").strip()
        start = parse_date(start_str)
        if start: break
        print("[ERROR] Invalid date format. Use YYYY-MM-DD.")
        
    while True:
        end_str = input("Enter End Date (YYYY-MM-DD): ").strip()
        end = parse_date(end_str)
        if not end:
            print("[ERROR] Invalid date format. Use YYYY-MM-DD.")
            continue
        if end < start:
            print("[ERROR] End date cannot be before start date.")
            continue
        break
        
    avail = calculate_item_availability(item['item_id'], start_str, end_str)
    units = load_json('equipment_units.json')
    total_unavailable = len([u for u in units if u['item_id'] == item['item_id'] and u['status'] in ['Maintenance', 'Broken']])
    total_stock = max(0, item['total_quantity'] - total_unavailable)
    
    print(f"\nAvailability for '{item['name']}' ({item['item_id']}) from {start_str} to {end_str}:")
    print(f"Total Catalog Stock   : {item['total_quantity']}")
    print(f"Broken/Maintenance   : {total_unavailable}")
    print(f"Effective Total Stock: {total_stock}")
    print(f"Available Quantity   : {avail}")
    print(f"Booked Quantity      : {total_stock - avail}")
    
    if total_stock - avail > 0:
        show_conflicting_bookings(item['item_id'], start, end)

def view_availability_report_cli():
    inventory = load_json('inventory.json')
    if not inventory:
        if inventory is None: return
        print("\nInventory is empty.")
        return
        
    print("\n--- View Availability Report ---")
    while True:
        start_str = input("Enter Start Date (YYYY-MM-DD): ").strip()
        start = parse_date(start_str)
        if start: break
        print("[ERROR] Invalid date format. Use YYYY-MM-DD.")
        
    while True:
        end_str = input("Enter End Date (YYYY-MM-DD): ").strip()
        end = parse_date(end_str)
        if not end:
            print("[ERROR] Invalid date format. Use YYYY-MM-DD.")
            continue
        if end < start:
            print("[ERROR] End date cannot be before start date.")
            continue
        break
        
    print("\n" + "="*95)
    print(f" AVAILABILITY REPORT FROM {start_str} TO {end_str}")
    print("="*95)
    print(f"{'Item ID':<8} | {'Item Name':<25} | {'Catalog Qty':<12} | {'Unavailable':<12} | {'Peak Booked':<12} | {'Available':<10}")
    print("-" * 95)
    for item in inventory:
        units = load_json('equipment_units.json')
        total_unavailable = len([u for u in units if u['item_id'] == item['item_id'] and u['status'] in ['Maintenance', 'Broken']])
        total_stock = max(0, item['total_quantity'] - total_unavailable)
        avail = calculate_item_availability(item['item_id'], start_str, end_str)
        peak_booked = total_stock - avail
        print(f"{item['item_id']:<8} | {item['name']:<25} | {item['total_quantity']:<12} | {total_unavailable:<12} | {peak_booked:<12} | {avail:<10}")
    print("="*95)

def show_available_items_cli():
    inventory = load_json('inventory.json')
    if not inventory:
        if inventory is None: return
        print("\nInventory is empty.")
        return
        
    print("\n--- Show Available Items ---")
    while True:
        start_str = input("Enter Start Date (YYYY-MM-DD): ").strip()
        start = parse_date(start_str)
        if start: break
        print("[ERROR] Invalid date format. Use YYYY-MM-DD.")
        
    while True:
        end_str = input("Enter End Date (YYYY-MM-DD): ").strip()
        end = parse_date(end_str)
        if not end:
            print("[ERROR] Invalid date format. Use YYYY-MM-DD.")
            continue
        if end < start:
            print("[ERROR] End date cannot be before start date.")
            continue
        break
        
    print("\n" + "="*80)
    print(f" AVAILABLE ITEMS FROM {start_str} TO {end_str}")
    print("="*80)
    print(f"{'Item ID':<8} | {'Item Name':<25} | {'Category':<15} | {'Available Qty':<15} | {'Rent/Day':<10}")
    print("-" * 80)
    count = 0
    for item in inventory:
        avail = calculate_item_availability(item['item_id'], start_str, end_str)
        if avail > 0:
            print(f"{item['item_id']:<8} | {item['name']:<25} | {item['category']:<15} | {avail:<15} | Rs.{item['rent_per_day']:<10}")
            count += 1
    if count == 0:
        print("No items available during this period.")
    print("="*80)

def calendar_view_cli():
    print("\n--- Calendar View (Bookings & Availability) ---")
    month_input = input("Enter Month (1-12) [Current]: ").strip()
    year_input = input("Enter Year (YYYY) [Current]: ").strip()
    
    now = datetime.now()
    try:
        month = int(month_input) if month_input else now.month
        if not (1 <= month <= 12):
            raise ValueError()
    except ValueError:
        print("[ERROR] Invalid month. Using current month.")
        month = now.month
        
    try:
        year = int(year_input) if year_input else now.year
        if not (1000 <= year <= 9999):
            raise ValueError()
    except ValueError:
        print("[ERROR] Invalid year. Using current year.")
        year = now.year
        
    print("\nWould you like to track availability for a specific item on the calendar?")
    choice = input("Enter 'y' to choose an item, or press Enter for general bookings calendar: ").strip().lower()
    item_id = None
    item_name = None
    if choice == 'y':
        inventory = load_json('inventory.json')
        item = find_record_by_name_or_id(inventory, "item_id", "name")
        if item:
            item_id = item['item_id']
            item_name = item['name']
            
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    print("\n=========================================================================")
    if item_id:
        print(f"   AVAILABILITY CALENDAR FOR: {item_name} ({item_id})")
        print("   Format: Day:(Available Stock)")
    else:
        print("   GENERAL BOOKINGS CALENDAR (Number of active bookings)")
        print("   Format: Day:[Active Bookings]")
    print(f"   {month_name} {year}")
    print("=========================================================================")
    print("  Mon       Tue       Wed       Thu       Fri       Sat       Sun")
    print("-------------------------------------------------------------------------")
    
    for week in cal:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += " " * 10
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                if item_id:
                    avail = calculate_item_availability(item_id, date_str, date_str)
                    val = f"{day}:({avail})"
                else:
                    bookings = load_json('bookings.json')
                    n_bookings = sum(1 for b in bookings if b.get('status') != 'Cancelled' and b['delivery_date'] <= date_str <= b['return_date'])
                    val = f"{day}:[{n_bookings}]"
                week_str += f"{val:<10}"
        print(week_str)
    print("=========================================================================")

def availability_menu():
    while True:
        print("\n--- Availability & Scheduling ---")
        print("1. Check Item Availability for Dates")
        print("2. View Availability Report for Date Range")
        print("3. Show Available Items for Date Range")
        print("4. Calendar-based Booking Check")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect an Option (1-5): ")
        if choice == '1': check_item_availability_cli()
        elif choice == '2': view_availability_report_cli()
        elif choice == '3': show_available_items_cli()
        elif choice == '4': calendar_view_cli()
        elif choice == '5': break
        else: print("Invalid choice, please select 1-5.")

# --- Main Program Menu ---

def main_menu():
    while True:
        print("\n==============================================")
        print("   SHARMAJI TENT HOUSE - MANAGEMENT SYSTEM   ")
        print("==============================================")
        print("1. Customer Management")
        print("2. Inventory Management")
        print("3. Equipment Unit Management")
        print("4. Booking Management")
        print("5. Availability & Scheduling")
        print("6. Payments, Returns & Damage Tracking")
        print("7. Exit")
        
        choice = input("\nSelect an Option (1-7): ")

        if choice == '1':
            customer_menu()
        elif choice == '2':
            inventory_menu()
        elif choice == '3':
            equipment_menu()
        elif choice == '4':
            booking_menu()
        elif choice == '5':
            availability_menu()
        elif choice == '6':
            payments_returns_menu()
        elif choice == '7':
            print("Thank you for using the system. Goodbye!")
            break
        else:
            print("Invalid choice, please select 1-7.")

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
