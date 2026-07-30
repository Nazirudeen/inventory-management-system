from flask import Flask, jsonify,render_template
from auth.auth_routes import auth_bp
from products.product_routes import product_bp
from billing.billing_routes import billing_bp
from sales.sales_routes import sales_bp

app = Flask(__name__)
app.secret_key = "inventory-secret-key"

# -------------------------------------------------
# REGISTER BACKEND BLUEPRINTS (APIs)
# -------------------------------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(product_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(sales_bp)

# -------------------------------------------------
# FRONTEND PAGE ROUTES
# -------------------------------------------------

# Login page (FIRST PAGE)
@app.route('/')
def login_page():
    return render_template('index.html')



# Signup page
@app.route('/signup')
def signup_page():
    return render_template('signup.html')


# Dashboard page
@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')


# Product management page
@app.route('/products-page')
def products_page():
    return render_template('products.html')


# Billing page
@app.route('/billing-page')
def billing_page():
    return render_template('billing.html')


# Sales report page
@app.route('/sales-page')
def sales_page():
    return render_template('sales.html')

# -------------------------------------------------
# APP START
# -------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
