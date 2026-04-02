import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(SCRIPT_DIR, "raw.txt"), "r", encoding="utf-8") as file:
    receipt_text = file.read()


# 1. Extract date and time
date_time_match = re.search(r'Время:\s*(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}:\d{2})', receipt_text)
receipt_date = date_time_match.group(1) if date_time_match else "N/A"
receipt_time = date_time_match.group(2) if date_time_match else "N/A"


# 2. Extract store info
store_match = re.search(r'Филиал\s+(.*)', receipt_text)
store_name = store_match.group(1).strip() if store_match else "N/A"

bin_match = re.search(r'БИН\s+(\d+)', receipt_text)
bin_number = bin_match.group(1) if bin_match else "N/A"

receipt_match = re.search(r'Чек\s*№(\d+)', receipt_text)
receipt_number = receipt_match.group(1) if receipt_match else "N/A"


# 3. Extract all products: number, name, quantity, unit price, subtotal
# Pattern: item number, then product name on next line, then qty x price
product_pattern = re.compile(
    r'^(\d+)\.\s*\n'              # item number
    r'(.+?)\s*\n'                 # product name
    r'(\d+,\d+)\s*x\s*([\d\s]+,\d+)\s*\n'  # qty x unit_price
    r'([\d\s]+,\d+)',             # subtotal
    re.MULTILINE
)

products = []
for match in product_pattern.finditer(receipt_text):
    item_number = int(match.group(1))
    product_name = match.group(2).strip()
    quantity = float(match.group(3).replace(",", "."))
    unit_price = float(match.group(4).replace(" ", "").replace(",", "."))
    subtotal = float(match.group(5).replace(" ", "").replace(",", "."))
    products.append({
        "number": item_number,
        "name": product_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "subtotal": subtotal,
    })


# 4. Extract all prices (subtotals from the receipt)
all_prices = [p["subtotal"] for p in products]

# 5. Calculate total
calculated_total = sum(all_prices)

# Extract the receipt's own total for comparison
total_match = re.search(r'ИТОГО:\s*\n\s*([\d\s]+,\d+)', receipt_text)
receipt_total = float(total_match.group(1).replace(" ", "").replace(",", ".")) if total_match else 0


# 6. Find payment method
payment_match = re.search(r'(Банковская карта|Наличные|Безналичная оплата)', receipt_text)
payment_method = payment_match.group(1) if payment_match else "N/A"


# 7. Extract address
address_match = re.search(r'г\.\s*(.+)', receipt_text)
address = address_match.group(0).strip() if address_match else "N/A"


# --- Structured output ---

print("=" * 60)
print(f"{'RECEIPT PARSER':^60}")
print("=" * 60)

print(f"\n  Store:    {store_name}")
print(f"  BIN:      {bin_number}")
print(f"  Receipt:  #{receipt_number}")
print(f"  Date:     {receipt_date}")
print(f"  Time:     {receipt_time}")
print(f"  Address:  {address}")
print(f"  Payment:  {payment_method}")

print(f"\n{'-' * 60}")
print(f"  {'#':<4} {'Product':<35} {'Qty':>4} {'Price':>8} {'Total':>8}")
print(f"{'-' * 60}")

for p in products:
    qty_str = f"{p['quantity']:.0f}" if p["quantity"] == int(p["quantity"]) else f"{p['quantity']}"
    print(f"  {p['number']:<4} {p['name'][:35]:<35} {qty_str:>4} {p['unit_price']:>8.2f} {p['subtotal']:>8.2f}")

print(f"{'-' * 60}")
print(f"  {'Calculated total:':<44} {calculated_total:>12,.2f}")
print(f"  {'Receipt total:':<44} {receipt_total:>12,.2f}")
print(f"  {'Match:':<44} {'Yes' if calculated_total == receipt_total else 'No':>12}")
print(f"  {'Items count:':<44} {len(products):>12}")
print("=" * 60)