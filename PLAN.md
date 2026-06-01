# 1. Three-Sentence Specification

This program will manage bookings, inventory, payments, returns, and damaged items for Sharma Tent House using Python and JSON files.

Rakesh ji and Ankit both use the system, but they need different things. Rakesh ji needs quick answers about customer bookings and item availability, while Ankit enters bookings, payments, returns, and damage records.

The project will be complete when the system can avoid overlapping bookings and save all data permanently.



# 2. Information The Program Will Store

### Customer Details

* Customer ID
* Customer Name
* Phone Number
* Address

### Item Details

* Item ID
* Item Name
* Category
* Total Quantity
* Rent Per Day
* Damage Charge
* Discount (if given)

### Individual Equipment Details 

* Unit ID
* Item ID
* Unit Name
* Status

### Booking Details

* Booking ID
* Customer ID
* Event Type
* Event Location
* Booking Date
* Delivery Date
* Return Date
* Total Amount
* Deposit Paid
* Remaining Amount
* Discount
* Booking Status

### Booking Item Details

* Booking Item ID
* Booking ID
* Item ID
* Quantity
* Price Per Day
* Total Days
* Total

### Payment Details

* Payment ID
* Booking ID
* Payment Amount
* Payment Date

### Return & Damage Material

* Return ID
* Booking ID
* Item ID
* Returned Quantity
* Damaged Quantity
* Missing Quantity
* Late Charges
* Extra Charges



# 3. How The Data Connects

* One customer can have many bookings.
* Each booking belongs to one customer.
* One booking can contain many booking items.
* Each booking item links a booking to an inventory item.
* One booking can have many payment records.
* Each payment belongs to one booking.
* One booking can have one or more return records.
* Each return record links back to a booking and an item.
* Damaged or missing items are recorded through return records.



# 4. File Structure

The system will use separate JSON files:

customers.json

inventory.json

equipment_units.json

bookings.json

booking_items.json

payments.json

returns.json

### Sample JSON Data

customers.json


[
  {
    "customer_id": 1,
    "name": "Amit Agarwal",
    "phone": "9876543210"
  }
]


bookings.json

[
  {
    "booking_id": 101,
    "customer_id": 1,
    "delivery_date": "2026-12-18",
    "return_date": "2026-12-20"
  }
]


booking_items.json


[
  {
    "booking_id": 101,
    "item_id": 5,
    "quantity": 100
  }
]


payments.json


[
  {
    "payment_id": 1,
    "booking_id": 101,
    "payment_amount": 5000
  }
]


If the business grows to 5,000 bookings per year, JSON files may become slow because the program must read and search large files every time. At that stage, a database system would be more efficient.


# 5. Operations

1. Add customer
2. Booking
3. Check item availability
4. Prevent overbooking (date can be marked on calendar)
5. Add items in booking
6. Remove items from booking
7. Cancel booking
8. Record full payment
9. Check how many items were given and returned
10. Record damaged items
11. Record missing items
12. Add late charges
13. Show todays deliveries and return items
14. Show available items
15. Show pending payments
16. Prevent closing booking if items are missing
17. Add discount (if given) in payment



# 6. Things That Can Go Wrong

1. Data file missing → Create an empty JSON file automatically and continue.
2. Invalid date entered → Show an error message and ask the user to enter the date again.
3. Negative quantity entered → Reject the value and ask for a valid quantity.
4. Return quantity greater than issued quantity → Show an error and prevent saving.
5. Booking cancelled after deposit → Ask the user to confirm refund or cancellation policy.
6. Customer ID not found → Show an error and stop booking creation.
7. Item ID not found → Show an error and ask for a valid item.
8. Payment amount greater than remaining balance → Reject the payment amount.
9. Duplicate booking ID → Generate or request a different booking ID.
10. Overlapping booking exceeds available quantity → Prevent booking and show availability conflict.
11. Missing JSON data field → Show an error and skip invalid record.
12. Return recorded before delivery date → Reject the entry and ask for correct dates.



# 7. One Thing I Don’t Know Yet

How to efficiently calculate item availability for overlapping booking dates using only JSON files and Python, and how to add a calendar and calender view in the terminal to display bookings and availability.
