import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from db import execute_query, test_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", "cs340_dev_secret"))

# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    total_products  = execute_query("SELECT COUNT(*) AS cnt FROM Product", fetch="one")["cnt"]
    total_customers = execute_query("SELECT COUNT(*) AS cnt FROM Customer", fetch="one")["cnt"]
    total_orders    = execute_query("SELECT COUNT(*) AS cnt FROM Orders", fetch="one")["cnt"]
    total_revenue   = execute_query("SELECT COALESCE(SUM(total_amount),0) AS rev FROM Orders", fetch="one")["rev"]
    return render_template("index.html",
                           total_products=total_products,
                           total_customers=total_customers,
                           total_orders=total_orders,
                           total_revenue=total_revenue)

# ---------------------------------------------------------------------------
# PRODUCTS
# ---------------------------------------------------------------------------

@app.route("/products")
def products():
    rows = execute_query("SELECT * FROM Product ORDER BY product_id", fetch="all")
    return render_template("products.html", products=rows)


@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        desc     = request.form.get("description", "").strip()
        price    = request.form.get("price", "0")
        stock    = request.form.get("stock_quantity", "0")
        category = request.form.get("category", "").strip()
        if not name:
            flash("Product name is required.", "danger")
            return redirect(url_for("add_product"))
        try:
            execute_query(
                """INSERT INTO Product (name, description, price, stock_quantity, category)
                   VALUES (%s, %s, %s, %s, %s)""",
                (name, desc or None, float(price), int(stock), category or None)
            )
            flash("Product added successfully.", "success")
            return redirect(url_for("products"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("product_form.html", product=None, action="Add")


@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = execute_query("SELECT * FROM Product WHERE product_id=%s", (product_id,), fetch="one")
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for("products"))
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        desc     = request.form.get("description", "").strip()
        price    = request.form.get("price", "0")
        stock    = request.form.get("stock_quantity", "0")
        category = request.form.get("category", "").strip()
        if not name:
            flash("Product name is required.", "danger")
            return redirect(url_for("edit_product", product_id=product_id))
        try:
            execute_query(
                """UPDATE Product SET name=%s, description=%s, price=%s,
                   stock_quantity=%s, category=%s WHERE product_id=%s""",
                (name, desc or None, float(price), int(stock), category or None, product_id)
            )
            flash("Product updated.", "success")
            return redirect(url_for("products"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("product_form.html", product=product, action="Edit")


@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    try:
        execute_query("DELETE FROM Product WHERE product_id=%s", (product_id,))
        flash("Product deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete product: {e}", "danger")
    return redirect(url_for("products"))

# ---------------------------------------------------------------------------
# CUSTOMERS
# ---------------------------------------------------------------------------

@app.route("/customers")
def customers():
    rows = execute_query("SELECT * FROM Customer ORDER BY customer_id", fetch="all")
    return render_template("customers.html", customers=rows)


@app.route("/customers/add", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        contact   = request.form.get("contact_information", "").strip()
        if not full_name:
            flash("Full name is required.", "danger")
            return redirect(url_for("add_customer"))
        try:
            execute_query(
                "INSERT INTO Customer (full_name, contact_information) VALUES (%s, %s)",
                (full_name, contact or None)
            )
            flash("Customer added.", "success")
            return redirect(url_for("customers"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("customer_form.html", customer=None, action="Add")


@app.route("/customers/edit/<int:customer_id>", methods=["GET", "POST"])
def edit_customer(customer_id):
    customer = execute_query("SELECT * FROM Customer WHERE customer_id=%s", (customer_id,), fetch="one")
    if not customer:
        flash("Customer not found.", "warning")
        return redirect(url_for("customers"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        contact   = request.form.get("contact_information", "").strip()
        if not full_name:
            flash("Full name is required.", "danger")
            return redirect(url_for("edit_customer", customer_id=customer_id))
        try:
            execute_query(
                "UPDATE Customer SET full_name=%s, contact_information=%s WHERE customer_id=%s",
                (full_name, contact or None, customer_id)
            )
            flash("Customer updated.", "success")
            return redirect(url_for("customers"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("customer_form.html", customer=customer, action="Edit")


@app.route("/customers/delete/<int:customer_id>", methods=["POST"])
def delete_customer(customer_id):
    try:
        execute_query("DELETE FROM Customer WHERE customer_id=%s", (customer_id,))
        flash("Customer deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete customer: {e}", "danger")
    return redirect(url_for("customers"))

# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------

@app.route("/users")
def users():
    rows = execute_query(
        """SELECT u.user_id, u.username, u.created_at,
                  a.admin_id, a.privileges
           FROM Users u
           LEFT JOIN Admin a ON a.user_id = u.user_id
           ORDER BY u.user_id""",
        fetch="all"
    )
    return render_template("users.html", users=rows)


@app.route("/users/add", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        username   = request.form.get("username", "").strip()
        password   = request.form.get("password", "").strip()
        is_admin   = request.form.get("is_admin") == "1"
        privileges = request.form.get("privileges", "read-only").strip()
        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("add_user"))
        try:
            new_user = execute_query(
                "INSERT INTO Users (username, password_hash) VALUES (%s, %s) RETURNING user_id",
                (username, password), fetch="one"
            )
            if is_admin and new_user:
                execute_query(
                    "INSERT INTO Admin (user_id, privileges) VALUES (%s, %s)",
                    (new_user["user_id"], privileges)
                )
            flash("User added" + (" as admin." if is_admin else "."), "success")
            return redirect(url_for("users"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("user_form.html", user=None, action="Add")


@app.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    user = execute_query(
        """SELECT u.user_id, u.username, u.created_at, a.admin_id, a.privileges
           FROM Users u LEFT JOIN Admin a ON a.user_id = u.user_id
           WHERE u.user_id=%s""",
        (user_id,), fetch="one"
    )
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("users"))
    if request.method == "POST":
        username   = request.form.get("username", "").strip()
        password   = request.form.get("password", "").strip()
        is_admin   = request.form.get("is_admin") == "1"
        privileges = request.form.get("privileges", "read-only").strip()
        if not username:
            flash("Username is required.", "danger")
            return redirect(url_for("edit_user", user_id=user_id))
        try:
            if password:
                execute_query(
                    "UPDATE Users SET username=%s, password_hash=%s WHERE user_id=%s",
                    (username, password, user_id)
                )
            else:
                execute_query("UPDATE Users SET username=%s WHERE user_id=%s", (username, user_id))
            # Sync admin status
            if is_admin:
                if user["admin_id"]:
                    execute_query("UPDATE Admin SET privileges=%s WHERE user_id=%s", (privileges, user_id))
                else:
                    execute_query("INSERT INTO Admin (user_id, privileges) VALUES (%s, %s)", (user_id, privileges))
            else:
                if user["admin_id"]:
                    execute_query("DELETE FROM Admin WHERE user_id=%s", (user_id,))
            flash("User updated.", "success")
            return redirect(url_for("users"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("user_form.html", user=user, action="Edit")


@app.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    try:
        execute_query("DELETE FROM Users WHERE user_id=%s", (user_id,))
        flash("User deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete user: {e}", "danger")
    return redirect(url_for("users"))


@app.route("/users/promote/<int:user_id>", methods=["POST"])
def promote_user(user_id):
    privileges = request.form.get("privileges", "read-only").strip() or "read-only"
    try:
        existing = execute_query("SELECT admin_id FROM Admin WHERE user_id=%s", (user_id,), fetch="one")
        if existing:
            execute_query("UPDATE Admin SET privileges=%s WHERE user_id=%s", (privileges, user_id))
            flash("Admin privileges updated.", "success")
        else:
            execute_query("INSERT INTO Admin (user_id, privileges) VALUES (%s, %s)", (user_id, privileges))
            flash("User promoted to admin.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for("users"))


@app.route("/users/demote/<int:user_id>", methods=["POST"])
def demote_user(user_id):
    try:
        execute_query("DELETE FROM Admin WHERE user_id=%s", (user_id,))
        flash("Admin privileges removed.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for("users"))

# ---------------------------------------------------------------------------
# ORDERS
# ---------------------------------------------------------------------------

@app.route("/orders")
def orders():
    rows = execute_query(
        """SELECT o.order_id, c.full_name AS customer_name, u.username,
                  o.order_date, o.status, o.total_amount
           FROM Orders o
           JOIN Customer c ON c.customer_id = o.customer_id
           JOIN Users    u ON u.user_id     = o.user_id
           ORDER BY o.order_id DESC""",
        fetch="all"
    )
    return render_template("orders.html", orders=rows)


@app.route("/orders/create", methods=["GET", "POST"])
def create_order():
    customers_list = execute_query("SELECT customer_id, full_name FROM Customer ORDER BY full_name", fetch="all")
    users_list     = execute_query("SELECT user_id, username FROM Users ORDER BY username", fetch="all")
    products_list  = execute_query("SELECT product_id, name, price FROM Product ORDER BY name", fetch="all")

    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        user_id     = request.form.get("user_id")
        status      = request.form.get("status", "Pending")
        product_ids = request.form.getlist("product_id[]")
        quantities  = request.form.getlist("quantity[]")

        if not customer_id or not user_id:
            flash("Customer and user are required.", "danger")
            return render_template("order_form.html",
                                   customers=customers_list,
                                   users=users_list,
                                   products=products_list)

        if not product_ids:
            flash("At least one product must be selected.", "danger")
            return render_template("order_form.html",
                                   customers=customers_list,
                                   users=users_list,
                                   products=products_list)

        # Build line items and calculate total
        line_items = []
        total = 0.0
        for pid, qty in zip(product_ids, quantities):
            if not pid or not qty:
                continue
            qty = int(qty)
            if qty <= 0:
                continue
            product = execute_query("SELECT price FROM Product WHERE product_id=%s", (pid,), fetch="one")
            if not product:
                continue
            unit_price = float(product["price"])
            total += unit_price * qty
            line_items.append((int(pid), qty, unit_price))

        if not line_items:
            flash("No valid products/quantities provided.", "danger")
            return render_template("order_form.html",
                                   customers=customers_list,
                                   users=users_list,
                                   products=products_list)

        try:
            conn_result = execute_query(
                """INSERT INTO Orders (customer_id, user_id, status, total_amount)
                   VALUES (%s, %s, %s, %s) RETURNING order_id""",
                (int(customer_id), int(user_id), status, round(total, 2))
            )
            new_order_id = conn_result["order_id"]

            for (pid, qty, unit_price) in line_items:
                execute_query(
                    """INSERT INTO OrderItem (order_id, product_id, quantity, unit_price)
                       VALUES (%s, %s, %s, %s)""",
                    (new_order_id, pid, qty, unit_price)
                )

            flash(f"Order #{new_order_id} created successfully.", "success")
            return redirect(url_for("orders"))
        except Exception as e:
            flash(f"Error creating order: {e}", "danger")

    return render_template("order_form.html",
                           customers=customers_list,
                           users=users_list,
                           products=products_list)


@app.route("/orders/edit/<int:order_id>", methods=["GET", "POST"])
def edit_order(order_id):
    order = execute_query("SELECT * FROM Orders WHERE order_id=%s", (order_id,), fetch="one")
    if not order:
        flash("Order not found.", "warning")
        return redirect(url_for("orders"))
    if request.method == "POST":
        status = request.form.get("status", "Pending")
        try:
            execute_query("UPDATE Orders SET status=%s WHERE order_id=%s", (status, order_id))
            flash("Order status updated.", "success")
            return redirect(url_for("orders"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("order_edit.html", order=order)


@app.route("/orders/delete/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    try:
        # OrderItems cascade on delete, so just delete the order
        execute_query("DELETE FROM Orders WHERE order_id=%s", (order_id,))
        flash("Order deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete order: {e}", "danger")
    return redirect(url_for("orders"))


@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = execute_query(
        """SELECT o.order_id, c.full_name AS customer_name, u.username,
                  o.order_date, o.status, o.total_amount
           FROM Orders o
           JOIN Customer c ON c.customer_id = o.customer_id
           JOIN Users    u ON u.user_id     = o.user_id
           WHERE o.order_id=%s""",
        (order_id,), fetch="one"
    )
    if not order:
        flash("Order not found.", "warning")
        return redirect(url_for("orders"))
    items = execute_query(
        """SELECT oi.order_item_id, p.name AS product_name,
                  oi.quantity, oi.unit_price,
                  (oi.quantity * oi.unit_price) AS line_total
           FROM OrderItem oi
           JOIN Product p ON p.product_id = oi.product_id
           WHERE oi.order_id=%s""",
        (order_id,), fetch="all"
    )
    return render_template("order_detail.html", order=order, items=items)

# ---------------------------------------------------------------------------
# QUERY REPORTS  (40 queries)
# ---------------------------------------------------------------------------

# All queries indexed 1-40 with label, member, sql, and optional param info
QUERIES = [
    # ── Member 1 – Mahmood ──────────────────────────────────────────────────
    {
        "id": 1, "member": "Mahmood", "label": "Get all products",
        "sql": "SELECT * FROM Product ORDER BY product_id",
        "params": [], "param_fields": []
    },
    {
        "id": 2, "member": "Mahmood", "label": "Get all customers",
        "sql": "SELECT * FROM Customer ORDER BY customer_id",
        "params": [], "param_fields": []
    },
    {
        "id": 3, "member": "Mahmood", "label": "Get all orders",
        "sql": """SELECT o.order_id, c.full_name, o.order_date, o.status, o.total_amount
                  FROM Orders o JOIN Customer c ON c.customer_id=o.customer_id
                  ORDER BY o.order_id""",
        "params": [], "param_fields": []
    },
    {
        "id": 4, "member": "Mahmood", "label": "Products with low stock (< 10)",
        "sql": "SELECT * FROM Product WHERE stock_quantity < 10 ORDER BY stock_quantity",
        "params": [], "param_fields": []
    },
    {
        "id": 5, "member": "Mahmood", "label": "Completed orders",
        "sql": """SELECT o.order_id, c.full_name, o.order_date, o.total_amount
                  FROM Orders o JOIN Customer c ON c.customer_id=o.customer_id
                  WHERE o.status='Completed' ORDER BY o.order_id""",
        "params": [], "param_fields": []
    },
    {
        "id": 6, "member": "Mahmood", "label": "Total number of orders per customer",
        "sql": """SELECT c.full_name, COUNT(o.order_id) AS total_orders
                  FROM Customer c LEFT JOIN Orders o ON o.customer_id=c.customer_id
                  GROUP BY c.customer_id, c.full_name ORDER BY total_orders DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 7, "member": "Mahmood", "label": "Total revenue from all orders",
        "sql": "SELECT COALESCE(SUM(total_amount),0) AS total_revenue FROM Orders",
        "params": [], "param_fields": []
    },
    {
        "id": 8, "member": "Mahmood", "label": "Order details with product names",
        "sql": """SELECT o.order_id, c.full_name AS customer, p.name AS product,
                         oi.quantity, oi.unit_price, (oi.quantity*oi.unit_price) AS line_total
                  FROM Orders o
                  JOIN Customer c  ON c.customer_id=o.customer_id
                  JOIN OrderItem oi ON oi.order_id=o.order_id
                  JOIN Product p   ON p.product_id=oi.product_id
                  ORDER BY o.order_id""",
        "params": [], "param_fields": []
    },
    {
        "id": 9, "member": "Mahmood", "label": "Most sold product",
        "sql": """SELECT p.name, SUM(oi.quantity) AS total_sold
                  FROM OrderItem oi JOIN Product p ON p.product_id=oi.product_id
                  GROUP BY p.product_id, p.name ORDER BY total_sold DESC LIMIT 1""",
        "params": [], "param_fields": []
    },
    {
        "id": 10, "member": "Mahmood", "label": "Customers who made more than 1 order",
        "sql": """SELECT c.full_name, COUNT(o.order_id) AS order_count
                  FROM Customer c JOIN Orders o ON o.customer_id=c.customer_id
                  GROUP BY c.customer_id, c.full_name HAVING COUNT(o.order_id) > 1
                  ORDER BY order_count DESC""",
        "params": [], "param_fields": []
    },
    # ── Member 2 – Abdullah AlQahtani ───────────────────────────────────────
    {
        "id": 11, "member": "Abdullah AlQahtani", "label": "Get all users",
        "sql": "SELECT user_id, username, created_at FROM Users ORDER BY user_id",
        "params": [], "param_fields": []
    },
    {
        "id": 12, "member": "Abdullah AlQahtani", "label": "Get all admins",
        "sql": """SELECT a.admin_id, u.username, a.privileges
                  FROM Admin a JOIN Users u ON u.user_id=a.user_id ORDER BY a.admin_id""",
        "params": [], "param_fields": []
    },
    {
        "id": 13, "member": "Abdullah AlQahtani", "label": "Get products by category",
        "sql": "SELECT * FROM Product WHERE category=%s ORDER BY name",
        "params": ["category"], "param_fields": [{"name": "category", "label": "Category", "type": "text"}]
    },
    {
        "id": 14, "member": "Abdullah AlQahtani", "label": "Customers created in last 30 days",
        "sql": "SELECT * FROM Customer WHERE created_at >= NOW() - INTERVAL '30 days' ORDER BY created_at DESC",
        "params": [], "param_fields": []
    },
    {
        "id": 15, "member": "Abdullah AlQahtani", "label": "Pending orders",
        "sql": """SELECT o.order_id, c.full_name, o.order_date, o.total_amount
                  FROM Orders o JOIN Customer c ON c.customer_id=o.customer_id
                  WHERE o.status='Pending' ORDER BY o.order_date""",
        "params": [], "param_fields": []
    },
    {
        "id": 16, "member": "Abdullah AlQahtani", "label": "Total revenue per customer",
        "sql": """SELECT c.full_name, COALESCE(SUM(o.total_amount),0) AS revenue
                  FROM Customer c LEFT JOIN Orders o ON o.customer_id=c.customer_id
                  GROUP BY c.customer_id, c.full_name ORDER BY revenue DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 17, "member": "Abdullah AlQahtani", "label": "Orders with more than 1 item",
        "sql": """SELECT oi.order_id, COUNT(oi.order_item_id) AS item_count
                  FROM OrderItem oi GROUP BY oi.order_id HAVING COUNT(oi.order_item_id) > 1
                  ORDER BY item_count DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 18, "member": "Abdullah AlQahtani", "label": "Products never ordered",
        "sql": """SELECT p.product_id, p.name, p.category, p.stock_quantity
                  FROM Product p
                  WHERE p.product_id NOT IN (SELECT DISTINCT product_id FROM OrderItem)
                  ORDER BY p.name""",
        "params": [], "param_fields": []
    },
    {
        "id": 19, "member": "Abdullah AlQahtani", "label": "Average product price per category",
        "sql": """SELECT category, ROUND(AVG(price),2) AS avg_price, COUNT(*) AS product_count
                  FROM Product WHERE category IS NOT NULL
                  GROUP BY category ORDER BY avg_price DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 20, "member": "Abdullah AlQahtani", "label": "Orders created per user",
        "sql": """SELECT u.username, COUNT(o.order_id) AS orders_created
                  FROM Users u LEFT JOIN Orders o ON o.user_id=u.user_id
                  GROUP BY u.user_id, u.username ORDER BY orders_created DESC""",
        "params": [], "param_fields": []
    },
    # ── Member 3 – Suliman ──────────────────────────────────────────────────
    {
        "id": 21, "member": "Suliman", "label": "Products with stock > 50",
        "sql": "SELECT * FROM Product WHERE stock_quantity > 50 ORDER BY stock_quantity DESC",
        "params": [], "param_fields": []
    },
    {
        "id": 22, "member": "Suliman", "label": "Orders created in last 30 days",
        "sql": """SELECT o.order_id, c.full_name, o.order_date, o.status, o.total_amount
                  FROM Orders o JOIN Customer c ON c.customer_id=o.customer_id
                  WHERE o.order_date >= NOW() - INTERVAL '30 days'
                  ORDER BY o.order_date DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 23, "member": "Suliman", "label": "Customers with Gmail accounts",
        "sql": "SELECT * FROM Customer WHERE contact_information ILIKE '%@gmail.com%' ORDER BY full_name",
        "params": [], "param_fields": []
    },
    {
        "id": 24, "member": "Suliman", "label": "Orders with total_amount > 500",
        "sql": """SELECT o.order_id, c.full_name, o.order_date, o.status, o.total_amount
                  FROM Orders o JOIN Customer c ON c.customer_id=o.customer_id
                  WHERE o.total_amount > 500 ORDER BY o.total_amount DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 25, "member": "Suliman", "label": "Products cheaper than 100",
        "sql": "SELECT * FROM Product WHERE price < 100 ORDER BY price",
        "params": [], "param_fields": []
    },
    {
        "id": 26, "member": "Suliman", "label": "Top 3 most expensive products",
        "sql": "SELECT name, price, category FROM Product ORDER BY price DESC LIMIT 3",
        "params": [], "param_fields": []
    },
    {
        "id": 27, "member": "Suliman", "label": "Customers with highest spending",
        "sql": """SELECT c.full_name, SUM(o.total_amount) AS total_spent
                  FROM Customer c JOIN Orders o ON o.customer_id=c.customer_id
                  GROUP BY c.customer_id, c.full_name ORDER BY total_spent DESC LIMIT 10""",
        "params": [], "param_fields": []
    },
    {
        "id": 28, "member": "Suliman", "label": "Average order value",
        "sql": "SELECT ROUND(AVG(total_amount),2) AS avg_order_value FROM Orders",
        "params": [], "param_fields": []
    },
    {
        "id": 29, "member": "Suliman", "label": "Total products sold per category",
        "sql": """SELECT p.category, SUM(oi.quantity) AS total_sold
                  FROM OrderItem oi JOIN Product p ON p.product_id=oi.product_id
                  WHERE p.category IS NOT NULL
                  GROUP BY p.category ORDER BY total_sold DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 30, "member": "Suliman", "label": "Orders with more than 2 distinct products",
        "sql": """SELECT oi.order_id, COUNT(DISTINCT oi.product_id) AS distinct_products
                  FROM OrderItem oi GROUP BY oi.order_id
                  HAVING COUNT(DISTINCT oi.product_id) > 2
                  ORDER BY distinct_products DESC""",
        "params": [], "param_fields": []
    },
    # ── Member 4 – Abdullah Altorifi ────────────────────────────────────────
    {
        "id": 31, "member": "Abdullah Altorifi", "label": "Products created in last 30 days",
        "sql": "SELECT * FROM Product WHERE created_at >= NOW() - INTERVAL '30 days' ORDER BY created_at DESC",
        "params": [], "param_fields": []
    },
    {
        "id": 32, "member": "Abdullah Altorifi", "label": "Cancelled orders",
        "sql": """SELECT o.order_id, c.full_name, o.order_date, o.total_amount
                  FROM Orders o JOIN Customer c ON c.customer_id=o.customer_id
                  WHERE o.status='Cancelled' ORDER BY o.order_date DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 33, "member": "Abdullah Altorifi", "label": "Orders for a selected customer",
        "sql": """SELECT o.order_id, o.order_date, o.status, o.total_amount
                  FROM Orders o WHERE o.customer_id=%s ORDER BY o.order_date DESC""",
        "params": ["customer_id"],
        "param_fields": [{"name": "customer_id", "label": "Customer ID", "type": "number"}]
    },
    {
        "id": 34, "member": "Abdullah Altorifi", "label": "Products with stock between 5 and 20",
        "sql": "SELECT * FROM Product WHERE stock_quantity BETWEEN 5 AND 20 ORDER BY stock_quantity",
        "params": [], "param_fields": []
    },
    {
        "id": 35, "member": "Abdullah Altorifi", "label": "Users created in last 30 days",
        "sql": "SELECT user_id, username, created_at FROM Users WHERE created_at >= NOW() - INTERVAL '30 days' ORDER BY created_at DESC",
        "params": [], "param_fields": []
    },
    {
        "id": 36, "member": "Abdullah Altorifi", "label": "Revenue by product category",
        "sql": """SELECT p.category, SUM(oi.quantity * oi.unit_price) AS category_revenue
                  FROM OrderItem oi JOIN Product p ON p.product_id=oi.product_id
                  WHERE p.category IS NOT NULL
                  GROUP BY p.category ORDER BY category_revenue DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 37, "member": "Abdullah Altorifi", "label": "Customers who never placed orders",
        "sql": """SELECT c.customer_id, c.full_name, c.contact_information
                  FROM Customer c
                  WHERE c.customer_id NOT IN (SELECT DISTINCT customer_id FROM Orders)
                  ORDER BY c.full_name""",
        "params": [], "param_fields": []
    },
    {
        "id": 38, "member": "Abdullah Altorifi", "label": "Monthly revenue summary",
        "sql": """SELECT TO_CHAR(order_date, 'YYYY-MM') AS month,
                         COUNT(*) AS order_count,
                         SUM(total_amount) AS monthly_revenue
                  FROM Orders GROUP BY month ORDER BY month DESC""",
        "params": [], "param_fields": []
    },
    {
        "id": 39, "member": "Abdullah Altorifi", "label": "Most active user by number of orders created",
        "sql": """SELECT u.username, COUNT(o.order_id) AS orders_created
                  FROM Users u JOIN Orders o ON o.user_id=u.user_id
                  GROUP BY u.user_id, u.username ORDER BY orders_created DESC LIMIT 1""",
        "params": [], "param_fields": []
    },
    {
        "id": 40, "member": "Abdullah Altorifi", "label": "Products with highest stock quantity",
        "sql": "SELECT name, category, stock_quantity FROM Product ORDER BY stock_quantity DESC LIMIT 10",
        "params": [], "param_fields": []
    },
]

# Build a lookup dict for quick access
QUERY_MAP = {q["id"]: q for q in QUERIES}


@app.route("/queries", methods=["GET", "POST"])
def queries():
    result_rows   = []
    result_keys   = []
    selected_q    = None
    param_values  = {}
    error_msg     = None

    query_id = request.values.get("query_id", type=int)
    if query_id and query_id in QUERY_MAP:
        selected_q = QUERY_MAP[query_id]
        # Collect param values from form
        for p in selected_q["params"]:
            param_values[p] = request.values.get(p, "")

        # Only run if all required params are provided
        missing = [p for p in selected_q["params"] if not param_values.get(p)]
        if not missing:
            try:
                sql    = selected_q["sql"]
                params = tuple(param_values[p] for p in selected_q["params"])
                rows   = execute_query(sql, params if params else None, fetch="all")
                if rows:
                    result_rows = rows
                    result_keys = list(rows[0].keys())
            except Exception as e:
                error_msg = str(e)

    # Group queries by member for the sidebar
    from collections import OrderedDict
    grouped = OrderedDict()
    for q in QUERIES:
        grouped.setdefault(q["member"], []).append(q)

    return render_template("queries.html",
                           grouped=grouped,
                           selected_q=selected_q,
                           result_rows=result_rows,
                           result_keys=result_keys,
                           param_values=param_values,
                           error_msg=error_msg)


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ok, err = test_connection()
    if ok:
        print("[OK] Database connection successful")
    else:
        print(f"[FAIL] Database connection failed: {err}")
    app.run(debug=True)
