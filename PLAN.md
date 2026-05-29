## 1. Three-Sentence Specification

This program will manage bookings, inventory, payments, returns, and damaged items for Sharma Tent House using Python and JSON files.
Both Rakesh ji and Ankit can use the system
The project will be complete when the system can avoid overlapping bookings and save all data permanently.



## 2. Information The Program Will Store

### Customer Details

* Customer ID
* Customer Name
* Phone Number
* Address


### item Details

* Item ID
* Item Name
* Category
* Total Quantity
* Available Quantity
* Rent Per Day
* Damage Charge
* discount (if givem)

### Booking Details

* Booking ID
* Customer Name
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

* Booking ID
* Item Name
* Quantity
* Price Per Day
* Total Days
* total

### Payment Details

* Payment ID
* Booking ID
* Payment Amount
* Payment Date


### Return & Damage material

* Returned Quantity
* Damaged Quantity
* Missing Quantity
* Late Charges
* Extra Charges



## 3. How The Data Connects

* One booking can contain many items
* track pending payment
* damaged or missin items


## 4. File Structure

The system will use separate JSON files:
customers.json 
inventory.json
bookings.json
booking_items.json
payments.json
returns.json




## 5. Operations

1. Add customer
2. booking
3. Check item availability
4. Prevent overbooking (date can be marked on calender)
5. Add items in booking
6. Remove items booking
7. Cancel booking
8. Record full payment
9. check how many items ievn and returned
10. Record damaged items
11. Record missing items
12. Add late charges
13. Show today's deliveries and return items
14. Show available items
15. Show pending payments
16. Prevent closing booking if items are missing
17. add discount (if given) in payment


## 6. Things That Can Go Wrong

1. data file missing 
2. Invalid date entered 
4. Negative quantity entered (error)
8. damage return quantity entered 
9. Booking cancelled after deposit 


## 7. One Thing I Don’t Know Yet
overlapping booking dates using only JSON files and Python (adding calender and calculatorto the terminal)
