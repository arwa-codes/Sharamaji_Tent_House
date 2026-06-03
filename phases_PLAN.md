## PHASE 1 – FOUNDATION & DATA MANAGEMENT

Goal:
Build the basic structure of the system and store data permanently using JSON files.

Features:
- Create JSON files automatically if missing
- Load and save JSON data
- Customer Management
  - Add Customer
  - View Customer
  - Search Customer
- Inventory Management
  - Add Item
  - View Items
  - Update Item Details
- Equipment Unit Management
  - Add Equipment Units
  - Change Unit Status

Error Handling:
- Missing JSON file
- Duplicate IDs
- Invalid Item ID
- Invalid Customer ID


## PHASE 2 – BOOKING SYSTEM

Goal:
Create and manage customer bookings and booking items while ensuring valid availability before saving bookings.

Features:
- Create Booking
- Add Booking Items
- Remove Booking Items
- Cancel Booking
- Calculate Total Amount
- Record Deposit Payment
- Store Booking Status
- Check Item Availability
- Check Date Overlap
- Prevent Overbooking During Booking Creation

Data Used:
- customers.json
- bookings.json
- booking_items.json

Error Handling:
- Customer not found
- Item not found
- Invalid dates
- Negative quantity
- Overlapping booking exceeds available stock


## PHASE 3 – AVAILABILITY & SCHEDULING

Goal:
Provide availability tracking, booking conflict reporting, and calendar-based scheduling tools.

Features:
- Show Available Quantity
- Booking Conflict Detection
- Availability Reports
- Show Available Items
- Calendar-based Booking Check in Terminal
- Calendar View for Bookings and Availability

Related Requirements:
- Show available items
- Display bookings and availability in a calendar view

Error Handling:
- Invalid date range
- Return before delivery date


## PHASE 4 – PAYMENTS, RETURNS & DAMAGE TRACKING

Goal:
Manage payments, returned items, damaged items, and pending balances.

Features:
- Record Full Payment
- Record Partial Payment
- Calculate Pending Payments
- Record Returned Items
- Record Damaged Items
- Record Missing Items
- Add Late Charges
- Add Extra Charges
- Apply Discount
- Prevent Closing Booking if Items Are Missing

Data Used:
- payments.json
- returns.json

Error Handling:
- Payment exceeds remaining balance
- Return quantity greater than issued quantity
- Invalid return records


## PHASE 5 – REPORTS, DASHBOARD & FINAL INTEGRATION

Goal:
Provide daily operational reports, availability reports, and complete system integration.

Features:
- Show Today's Deliveries
- Show Today's Returns
- Show Pending Payments
- Show Available Inventory
- Booking Summary
- Customer Booking History
- Damage Reports
- Revenue Summary
- Final System Testing

Final Validation:
- All data saved permanently
- No overbooking possible
- Payments tracked correctly
- Returns managed correctly
- Reports generated successfully
