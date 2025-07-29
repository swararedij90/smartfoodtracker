from flask import Flask, render_template, request, redirect, url_for, jsonify
from db import get_db_connection  # MySQL connection
from datetime import date, datetime

app = Flask(__name__, template_folder="templates")

# ---------------- Home Page ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- User Login ----------------
@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='User'", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for("user_dashboard"))
        else:
            error = "Invalid username or password!"
    return render_template("user_login.html", error=error)


# ---------------- Admin Login ----------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='Admin'", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid username or password!"
    return render_template("admin_login.html", error=error)


# ---------------- User Dashboard ----------------
@app.route("/user_dashboard")
def user_dashboard():
    today = date.today()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, category, purchase_date, expiry_date, quantity, consumed FROM inventory")
    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        item = {
            "item_name": row[0],
            "category": row[1],
            "purchase_date": row[2],
            "expiry_date": row[3],
            "quantity": row[4],
            "consumed": row[5]
        }

        # Ensure expiry_date is a date object
        if isinstance(item["expiry_date"], str):
            item["expiry_date"] = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()

        days_left = (item["expiry_date"] - today).days if item["expiry_date"] else None

        # Only red if 0–3 days left (not expired)
        item["expiring"] = days_left is not None and 0 <= days_left < 4
        item["days_left"] = days_left

        items.append(item)

    # Group by category
    grouped_items = {}
    for item in items:
        grouped_items.setdefault(item["category"], []).append(item)

    return render_template("user_dashboard.html", grouped_items=grouped_items)


# ---------------- Admin Dashboard ----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch simple stats
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN DATEDIFF(expiry_date, CURDATE()) < 4 THEN 1 ELSE 0 END) FROM inventory")
    total_items, expiring_soon = cursor.fetchone()

    # Fetch category-wise totals
    cursor.execute("SELECT category, COUNT(*) FROM inventory GROUP BY category")
    categories = cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html",
                           total_items=total_items,
                           expiring_soon=expiring_soon,
                           categories=categories)


# ---------------- Recipe Suggestions API ----------------
recipes = {
    "Milk": {
        "name": "Pancakes",
        "ingredients": ["1 cup flour", "1 egg", "1 cup milk", "1 tbsp sugar", "Butter for frying"],
        "steps": [
            "Mix flour, sugar, egg, and milk into a smooth batter.",
            "Heat a pan and melt butter.",
            "Pour batter and cook until golden brown.",
            "Serve with syrup or fruits."
        ]
    },
    "Cheese": {
        "name": "Grilled Cheese Sandwich",
        "ingredients": ["2 bread slices", "Cheddar cheese", "Butter"],
        "steps": [
            "Spread butter on bread slices.",
            "Place cheese between slices.",
            "Grill until golden and cheese melts."
        ]
    }
}

@app.route("/get_recipe/<item_name>")
def get_recipe(item_name):
    recipe = recipes.get(item_name, {"name": "No Recipe Found", "ingredients": [], "steps": []})
    return jsonify(recipe)


if __name__ == "__main__":
    app.run(debug=True)