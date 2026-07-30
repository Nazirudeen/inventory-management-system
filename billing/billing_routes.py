from flask import Blueprint, request, jsonify, session
from db import get_db_connection

billing_bp = Blueprint('billing', __name__)

# -------------------------------------------------
# 🔐 Helper: login required
# -------------------------------------------------
def login_required():
    return 'user_id' in session


# -------------------------------------------------
# 🧾 CREATE BILL (ONE ROUTE ONLY)
# -------------------------------------------------
@billing_bp.route('/billing/create-bill', methods=['POST'])
def create_bill():

    if not login_required():
        return jsonify({
            "status": "error",
            "message": "Login required"
        }), 401

    data = request.json
    if not data:
        return jsonify({
            "status": "error",
            "message": "No data provided"
        }), 400

    items = data.get('items', [])
    payment_mode = data.get('payment_mode', 'Cash')

    if not items:
        return jsonify({
            "status": "error",
            "message": "No items provided"
        }), 400

    user_id = session['user_id']  # ✅ shop owner

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 🔹 Step 1: create empty sale
        cursor.execute("""
            INSERT INTO sales (user_id, total_amount, payment_mode)
            VALUES (%s, %s, %s)
        """, (user_id, 0, payment_mode))

        sale_id = cursor.lastrowid
        total_amount = 0

        # 🔹 Step 2: loop products
        for item in items:
            product_id = int(item['product_id'])
            quantity = int(item['quantity'])

            cursor.execute(
                "SELECT price, quantity FROM products WHERE product_id=%s",
                (product_id,)
            )
            product = cursor.fetchone()

            if not product:
                conn.rollback()
                return jsonify({
                    "status": "error",
                    "message": "Product not found"
                }), 404

            if quantity > product['quantity']:
                conn.rollback()
                return jsonify({
                    "status": "error",
                    "message": "Insufficient stock"
                }), 400

            item_total = product['price'] * quantity
            total_amount += item_total

            # 🔹 Step 3: insert sales_items
            cursor.execute("""
                INSERT INTO sales_items
                (sale_id, product_id, quantity, price, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (sale_id, product_id, quantity, product['price'], user_id))

            # 🔹 Step 4: update stock
            cursor.execute(
                "UPDATE products SET quantity = quantity - %s WHERE product_id=%s",
                (quantity, product_id)
            )

        # 🔹 Step 5: update final total
        cursor.execute("""
            UPDATE sales SET total_amount=%s WHERE sale_id=%s
        """, (total_amount, sale_id))

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "status": "success",
        "sale_id": sale_id,
        "total_amount": total_amount,
        "payment_mode": payment_mode
    })



# -------------------------------------------------
# 📜 SALES HISTORY (SHOP-WISE)
# -------------------------------------------------
@billing_bp.route('/billing/sales', methods=['GET'])
def sales_history():

    if not login_required():
        return jsonify({
            "status": "error",
            "message": "Login required"
        }), 401

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sale_id, sale_date, total_amount, payment_mode
        FROM sales
        WHERE user_id = %s
        ORDER BY sale_date DESC
    """, (user_id,))

    sales = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "status": "success",
        "total_sales": len(sales),
        "data": sales
    })


# -------------------------------------------------
# 📊 MONTHLY SALES REPORT (SHOP-WISE)
# -------------------------------------------------
@billing_bp.route('/billing/report/monthly', methods=['GET'])
def monthly_report():

    if not login_required():
        return jsonify({
            "status": "error",
            "message": "Login required"
        }), 401

    month = request.args.get('month')  # format: YYYY-MM
    if not month:
        return jsonify({
            "status": "error",
            "message": "Month required"
        }), 400

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) AS total_bills,
            IFNULL(SUM(total_amount), 0) AS total_sales
        FROM sales
        WHERE user_id = %s
          AND DATE_FORMAT(sale_date, '%%Y-%%m') = %s
    """, (user_id, month))

    report = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "status": "success",
        "report": {
            "month": month,
            "total_bills": report['total_bills'],
            "total_sales": float(report['total_sales'])
        }
    })
