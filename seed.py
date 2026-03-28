"""
seed.py – Insert sample data into all tables for demo/testing purposes.
Run once after creating the schema: python seed.py
"""

from db import execute_query

def seed():
    print("Seeding Users...")
    user_ids = []
    for username, password in [
        ("mahmood", "pass123"),
        ("abdullahq", "pass123"),
        ("suliman", "pass123"),
        ("abdullahalt", "pass123"),
    ]:
        row = execute_query(
            "INSERT INTO Users (username, password_hash) VALUES (%s, %s) "
            "ON CONFLICT (username) DO NOTHING RETURNING user_id",
            (username, password)
        )
        if row:
            user_ids.append(row["user_id"])

    # Fetch user ids in case they already existed
    all_users = execute_query("SELECT user_id FROM Users ORDER BY user_id", fetch="all")
    user_ids = [u["user_id"] for u in all_users]

    print("Seeding Admins...")
    if user_ids:
        execute_query(
            "INSERT INTO Admin (user_id, privileges) VALUES (%s, %s) "
            "ON CONFLICT (user_id) DO NOTHING",
            (user_ids[0], "full_access")
        )

    print("Seeding Products...")
    products = [
        ("Laptop Pro 15",    "High performance laptop",         1299.99, 25, "Electronics"),
        ("Wireless Mouse",   "Ergonomic wireless mouse",          29.99, 80, "Electronics"),
        ("USB-C Hub",        "7-port USB-C hub",                  49.99,  5, "Electronics"),
        ("Desk Chair",       "Ergonomic office chair",           349.99, 12, "Furniture"),
        ("Standing Desk",    "Height adjustable desk",           599.99,  8, "Furniture"),
        ("Notebook A5",      "200-page lined notebook",            4.99, 200, "Stationery"),
        ("Ballpoint Pens x10","Pack of 10 pens",                   3.99, 150, "Stationery"),
        ("Monitor 27\"",     "4K UHD monitor",                   799.99,  3, "Electronics"),
        ("Keyboard Mech",    "Mechanical keyboard TKL",          129.99, 18, "Electronics"),
        ("Webcam HD",        "1080p webcam with mic",             79.99, 30, "Electronics"),
        ("Bookshelf 5-tier", "Wooden 5-tier bookshelf",          189.99,  6, "Furniture"),
        ("Whiteboard A1",    "Magnetic whiteboard",               89.99, 40, "Stationery"),
    ]
    product_ids = []
    for name, desc, price, stock, category in products:
        row = execute_query(
            "INSERT INTO Product (name, description, price, stock_quantity, category) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING product_id",
            (name, desc, price, stock, category)
        )
        if row:
            product_ids.append(row["product_id"])

    if not product_ids:
        product_ids = [p["product_id"] for p in
                       execute_query("SELECT product_id FROM Product ORDER BY product_id", fetch="all")]

    print("Seeding Customers...")
    customers_data = [
        ("Ali Hassan",        "ali.hassan@gmail.com"),
        ("Sara Ahmed",        "sara.ahmed@outlook.com"),
        ("Omar Khalid",       "omar.khalid@gmail.com"),
        ("Nora Abdullah",     "nora.a@gmail.com"),
        ("Faisal Al-Mutairi", "faisal@company.com"),
        ("Lena Youssef",      "lena.y@gmail.com"),
        ("Khaled Mansour",    "khaled@domain.net"),
    ]
    customer_ids = []
    for full_name, contact in customers_data:
        row = execute_query(
            "INSERT INTO Customer (full_name, contact_information) VALUES (%s, %s) RETURNING customer_id",
            (full_name, contact)
        )
        if row:
            customer_ids.append(row["customer_id"])

    if not customer_ids:
        customer_ids = [c["customer_id"] for c in
                        execute_query("SELECT customer_id FROM Customer ORDER BY customer_id", fetch="all")]

    print("Seeding Orders + OrderItems...")
    if customer_ids and user_ids and product_ids:
        orders_data = [
            (customer_ids[0], user_ids[0], "Completed", [(product_ids[0], 1), (product_ids[1], 2)]),
            (customer_ids[1], user_ids[1], "Pending",   [(product_ids[3], 1)]),
            (customer_ids[0], user_ids[0], "Pending",   [(product_ids[8], 1), (product_ids[9], 1)]),
            (customer_ids[2], user_ids[2], "Completed", [(product_ids[5], 5), (product_ids[6], 3)]),
            (customer_ids[3], user_ids[3], "Cancelled", [(product_ids[7], 1)]),
            (customer_ids[4], user_ids[0], "Completed", [(product_ids[4], 1), (product_ids[2], 2)]),
            (customer_ids[5], user_ids[1], "Pending",   [(product_ids[10], 1)]),
        ]
        for customer_id, user_id, status, items in orders_data:
            total = 0.0
            line_items = []
            for pid, qty in items:
                p = execute_query("SELECT price FROM Product WHERE product_id=%s", (pid,), fetch="one")
                if p:
                    unit_price = float(p["price"])
                    total += unit_price * qty
                    line_items.append((pid, qty, unit_price))
            order_row = execute_query(
                "INSERT INTO Orders (customer_id, user_id, status, total_amount) "
                "VALUES (%s, %s, %s, %s) RETURNING order_id",
                (customer_id, user_id, status, round(total, 2))
            )
            if order_row:
                order_id = order_row["order_id"]
                for pid, qty, unit_price in line_items:
                    execute_query(
                        "INSERT INTO OrderItem (order_id, product_id, quantity, unit_price) "
                        "VALUES (%s, %s, %s, %s)",
                        (order_id, pid, qty, unit_price)
                    )

    print("Seeding complete!")


if __name__ == "__main__":
    seed()
