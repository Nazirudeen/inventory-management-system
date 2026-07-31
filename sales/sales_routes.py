from flask import Blueprint, jsonify, request, session
from db import get_db_connection

sales_bp = Blueprint('sales', __name__)

# -------------------------------------------------
# 🔐 LOGIN REQUIRED CHECK
# -------------------------------------------------
def login_required():
    return 'user_id' in session


# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def fetch_all(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def fetch_one(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


# -------------------------------------------------
# 1️⃣ VIEW ALL SOLD ITEMS (SHOP-WISE)
# -------------------------------------------------
@sales_bp.route('/sales/items', methods=['GET'])
def get_all_sold_items():

    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 401

    user_id = session['user_id']
    selected_date = request.args.get("date")  # 👈 get date

    conn = get_db_connection()
    cursor = conn.cursor()

    if selected_date:
        cursor.execute("""
            SELECT sale_id, sale_date, total_amount
            FROM sales
            WHERE user_id = %s
            AND DATE(sale_date) = %s
            ORDER BY sale_id DESC
        """, (user_id, selected_date))
    else:
        cursor.execute("""
            SELECT sale_id, sale_date, total_amount
            FROM sales
            WHERE user_id = %s
            ORDER BY sale_id DESC
        """, (user_id,))

    data = cursor.fetchall()
    if not data:
     cursor.close()
     conn.close()
     return jsonify({
        "status": "error",
        "message": "No bills found for this date"
    }), 404


    cursor.close()
    conn.close()

    return jsonify({
        "status": "success",
        "data": data
    })


# -------------------------------------------------
# 2️⃣ VIEW SINGLE BILL (SHOP-WISE SAFE)
# -------------------------------------------------
@sales_bp.route('/sales/<int:sale_id>', methods=['GET'])
def view_single_bill(sale_id):

    if not login_required():
        return jsonify({
            "status": "error",
            "message": "Login required"
        }), 401

    user_id = session['user_id']

    bill_query = """
        SELECT sale_id, sale_date, total_amount, payment_mode
        FROM sales
        WHERE sale_id = %s AND user_id = %s
    """

    bill = fetch_one(bill_query, (sale_id, user_id))

    if not bill:
        return jsonify({
            "status": "error",
            "message": "Bill not found"
        }), 404

    # ✅ FORMAT DATE HERE
    bill['sale_date'] = bill['sale_date'].strftime("%Y-%m-%d %H:%M:%S")

    items_query = """
        SELECT 
            p.product_name,
            si.quantity,
            si.price,
            (si.quantity * si.price) AS total
        FROM sales_items si
        JOIN products p ON si.product_id = p.product_id
        WHERE si.sale_id = %s AND si.user_id = %s
    """

    items = fetch_all(items_query, (sale_id, user_id))

    return jsonify({
        "status": "success",
        "bill": bill,
        "items": items
    })


# -------------------------------------------------
# 3️⃣ DAILY SALES REPORT (SHOP-WISE)
# -------------------------------------------------
@sales_bp.route('/sales/report/daily', methods=['GET'])
def daily_sales_report():

    if not login_required():
        return jsonify({
            "status": "error",
            "message": "Login required"
        }), 401

    date = request.args.get('date')  # YYYY-MM-DD

    if not date:
        return jsonify({
            "status": "error",
            "message": "Date parameter required (YYYY-MM-DD)"
        }), 400

    user_id = session['user_id']

    query = """
        SELECT 
            DATE(sale_date) AS sale_date,
            COUNT(*) AS total_bills,
            IFNULL(SUM(total_amount), 0) AS total_sales
        FROM sales
        WHERE DATE(sale_date) = %s
          AND user_id = %s
        GROUP BY DATE(sale_date)
    """

    report = fetch_one(query, (date, user_id))

    if not report:
        return jsonify({
            "status": "error",
            "message": "No sales found for this date"
        }), 404

    return jsonify({
        "status": "success",
        "report": report
    })


# -------------------------------------------------
# 4️⃣ MONTHLY SALES REPORT (SHOP-WISE)
# -------------------------------------------------
@sales_bp.route('/sales/report/monthly', methods=['GET'])
def monthly_report():

    if not login_required():
        return jsonify({"status": "error"}), 401

    user_id = session['user_id']
    month = request.args.get('month')   # 2026-01

    if not month:
        return jsonify({"status": "error"}), 400

    query = """
        SELECT 
            COUNT(*) AS total_bills,
            SUM(total_amount) AS total_sales
        FROM sales
        WHERE DATE_FORMAT(sale_date, '%%Y-%%m') = %s
        AND user_id = %s
    """

    result = fetch_one(query, (month, user_id))

    if not result:
        return jsonify({"status": "error"})

    return jsonify({
        "status": "success",
        "report": {
            "month": month,
            "total_bills": result["total_bills"] or 0,
            "total_sales": float(result["total_sales"] or 0)
        }
    })

