from flask import Blueprint, request, jsonify, session
from db import get_db_connection

product_bp = Blueprint('products', __name__)

# 🔐 Helper: check login
def require_login():
    user_id = session.get('user_id')
    if not user_id:
        return None, jsonify({"status": "error", "message": "Unauthorized"}), 401
    return user_id, None, None


# ➕ ADD PRODUCT
@product_bp.route('/products', methods=['POST'])
def add_product():
    user_id, err, code = require_login()
    if err:
        return err, code

    data = request.json
    name = data.get('product_name')
    price = data.get('price')
    qty = data.get('quantity')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO products 
           (product_name, price, quantity, user_id)
           VALUES (%s, %s, %s, %s)""",
        (name, price, qty, user_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Product added"})


# 📋 GET PRODUCTS (ONLY LOGGED-IN USER)
@product_bp.route('/products', methods=['GET'])
def get_products():
    user_id, err, code = require_login()
    if err:
        return err, code

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE user_id=%s",
        (user_id,)
    )
    products = cursor.fetchall()

    conn.close()

    return jsonify({"status": "success", "data": products})


# ✏️ UPDATE PRODUCT
@product_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    user_id, err, code = require_login()
    if err:
        return err, code

    data = request.json
    name = data.get('product_name')
    price = data.get('price')
    qty = data.get('quantity')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """UPDATE products 
           SET product_name=%s, price=%s, quantity=%s
           WHERE product_id=%s AND user_id=%s""",
        (name, price, qty, product_id, user_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Product updated"})


# 🗑️ DELETE PRODUCT
@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"status": "error", "message": "Login required"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM products WHERE product_id=%s AND user_id=%s",
            (product_id, user_id)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "status": "error",
                "message": "Product not found"
            }), 404

        return jsonify({
            "status": "success",
            "message": "Product deleted successfully"
        })

    except Exception:
        conn.rollback()
        return jsonify({
            "status": "error",
            "message": "Cannot delete this product because it has sales history."
        }), 400

    finally:
        cursor.close()
        conn.close()