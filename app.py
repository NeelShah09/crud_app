import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_here'
DATABASE = 'sales.db'

def create_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS mobile_details
                 (model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  brand_name TEXT NOT NULL,
                  model_name TEXT NOT NULL,
                  price REAL NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS customer_details
                 (customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  dob TEXT,
                  gender TEXT,
                  country TEXT,
                  state TEXT,
                  city TEXT,
                  contact_no TEXT,
                  email_id TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transaction_details
                 (tr_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  model_id INTEGER NOT NULL,
                  customer_id INTEGER NOT NULL,
                  quantity INTEGER NOT NULL,
                  date TEXT NOT NULL,
                  total_amount REAL NOT NULL,
                  FOREIGN KEY (model_id) REFERENCES mobile_details (model_id),
                  FOREIGN KEY (customer_id) REFERENCES customer_details (customer_id))''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_visualization():
    conn = get_db_connection()
    try:
        sales_data = conn.execute('''
            SELECT md.brand_name, SUM(td.total_amount) as total_sales, COUNT(td.tr_id) as transaction_count
            FROM transaction_details td
            JOIN mobile_details md ON td.model_id = md.model_id
            GROUP BY md.brand_name
            ORDER BY total_sales DESC
        ''').fetchall()
        
        # (Keep the rest of your existing visualization code here)
        
        img = BytesIO()
        plt.savefig(img, format='png', dpi=120, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return plot_url
    finally:
        conn.close()

def generate_analytics():
    conn = get_db_connection()
    try:
        plt.style.use('seaborn-v0_8')
        
        # Monthly trend plot
        monthly_buffer = BytesIO()
        plt.figure(figsize=(12, 6))
        
        monthly_data = conn.execute('''
            SELECT strftime('%Y-%m', date) as month, 
                   SUM(total_amount) as total
            FROM transaction_details
            GROUP BY month
            ORDER BY month
        ''').fetchall()
        
        months = [row['month'] for row in monthly_data]
        totals = [row['total'] for row in monthly_data]
        
        plt.plot(months, totals, marker='o', color='#4361ee', linewidth=2)
        plt.title('Monthly Sales Trend', fontweight='bold', pad=20)
        plt.xlabel('Month', fontsize=10)
        plt.ylabel('Revenue ($)', fontsize=10)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        plt.savefig(monthly_buffer, format='png', dpi=120)
        monthly_plot = base64.b64encode(monthly_buffer.getvalue()).decode()
        monthly_buffer.close()
        plt.close()

        # Top models plot
        models_buffer = BytesIO()
        plt.figure(figsize=(12, 7))
        
        top_models = conn.execute('''
            SELECT md.brand_name || ' ' || md.model_name as model,
                   SUM(td.quantity) as units_sold,
                   SUM(td.total_amount) as total_sales
            FROM transaction_details td
            JOIN mobile_details md ON td.model_id = md.model_id
            GROUP BY model
            ORDER BY units_sold DESC
            LIMIT 10
        ''').fetchall()
        
        models = [row['model'] for row in top_models]
        units = [row['units_sold'] for row in top_models]
        sales = [row['total_sales'] for row in top_models]
        
        colors = plt.cm.viridis_r([x / max(sales) for x in sales])
        bars = plt.barh(models, units, color=colors)
        
        plt.title('Top Selling Models by Units Sold', fontweight='bold', pad=20)
        plt.xlabel('Units Sold', fontsize=10)
        plt.ylabel('')
        plt.gca().invert_yaxis()
        
        # Add value labels
        for i, (unit, sale) in enumerate(zip(units, sales)):
            plt.text(unit + max(units)*0.01, i, 
                    f'{unit} units\n(${sale:,.0f})', 
                    va='center', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(models_buffer, format='png', dpi=120)
        models_plot = base64.b64encode(models_buffer.getvalue()).decode()
        models_buffer.close()
        plt.close()

        return monthly_plot, models_plot
    finally:
        conn.close()
        plt.close('all')

@app.route('/analytics-data')
def analytics_data():
    conn = get_db_connection()
    
    # Monthly data
    monthly = conn.execute('''
        SELECT strftime('%Y-%m', date) as month, 
               SUM(total_amount) as total
        FROM transaction_details
        GROUP BY month
        ORDER BY month
    ''').fetchall()
    
    # Top models data
    models = conn.execute('''
        SELECT md.brand_name || ' ' || md.model_name as model,
               SUM(td.quantity) as units_sold,
               SUM(td.total_amount) as total_sales
        FROM transaction_details td
        JOIN mobile_details md ON td.model_id = md.model_id
        GROUP BY model
        ORDER BY units_sold DESC
        LIMIT 10
    ''').fetchall()
    
    #  New brand distribution query
    brand_dist = conn.execute('''
        SELECT md.brand_name, SUM(td.total_amount) as total_sales
        FROM transaction_details td
        JOIN mobile_details md ON td.model_id = md.model_id
        GROUP BY md.brand_name
        ORDER BY total_sales DESC
    ''').fetchall()
    
    # New brand trends query
    brand_trends = conn.execute('''
        SELECT strftime('%Y-%m', td.date) as month,
               md.brand_name,
               SUM(td.total_amount) as total_sales
        FROM transaction_details td
        JOIN mobile_details md ON td.model_id = md.model_id
        GROUP BY month, md.brand_name
        ORDER BY month
    ''').fetchall()

    conn.close()
    
    trends = {}
    for row in brand_trends:
        brand = row['brand_name']
        if brand not in trends:
            trends[brand] = {'labels': [], 'values': []}
        trends[brand]['labels'].append(row['month'])
        trends[brand]['values'].append(float(row['total_sales']))
    
    return jsonify({
        'monthly': {
            'labels': [row['month'] for row in monthly],
            'values': [float(row['total']) for row in monthly]
        },
        'models': {
            'labels': [row['model'] for row in models],
            'values': [row['units_sold'] for row in models],
            'sales': [float(row['total_sales']) for row in models]
        },
        'brand_dist': {
            'labels': [row['brand_name'] for row in brand_dist],
            'values': [float(row['total_sales']) for row in brand_dist]
        },
        'brand_trends': trends
    })

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple authentication - in production use proper auth with password hashing
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    current_month = datetime.now().strftime('%Y-%m')
    
    transactions = conn.execute('''
        SELECT td.tr_id, td.date, md.brand_name, md.model_name, md.price, 
               td.quantity, td.total_amount, cd.name as customer_name
        FROM transaction_details td
        JOIN mobile_details md ON td.model_id = md.model_id
        JOIN customer_details cd ON td.customer_id = cd.customer_id
        WHERE strftime('%Y-%m', td.date) = ?
        ORDER BY td.date DESC
    ''', (current_month,)).fetchall()
    
    stats = conn.execute('''
        SELECT COUNT(*) as total_transactions,
            COALESCE(SUM(total_amount), 0) as total_revenue,
            COALESCE(AVG(total_amount), 0) as avg_sale,
            (SELECT md.brand_name 
             FROM mobile_details md
             JOIN transaction_details td ON md.model_id = td.model_id
             WHERE strftime('%Y-%m', td.date) = ?
             GROUP BY md.brand_name
             ORDER BY SUM(td.total_amount) DESC
             LIMIT 1) as top_brand
        FROM transaction_details
        WHERE strftime('%Y-%m', date) = ?
    ''', (current_month, current_month)).fetchone()
    
    models = conn.execute('SELECT model_id, brand_name, model_name FROM mobile_details').fetchall()
    customers = conn.execute('SELECT customer_id, name FROM customer_details').fetchall()
    conn.close()
    
    plot_url = generate_visualization() if transactions else ''
    monthly_plot, models_plot = generate_analytics() if transactions else ('', '')
    
    return render_template(
        'dashboard.html',
        transactions=transactions,
        plot_url=plot_url,
        monthly_plot=monthly_plot,
        models_plot=models_plot,
        stats=stats,
        models=models,
        customers=customers
    )

@app.route('/add_mobile', methods=['POST'])
def add_mobile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    brand_name = request.form['brand_name']
    model_name = request.form['model_name']
    price = float(request.form['price'])
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO mobile_details (brand_name, model_name, price)
        VALUES (?, ?, ?)
    ''', (brand_name, model_name, price))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/add_customer', methods=['POST'])
def add_customer():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    name = request.form['name']
    dob = request.form.get('dob', None)
    gender = request.form.get('gender', None)
    country = request.form.get('country', None)
    state = request.form.get('state', None)
    city = request.form.get('city', None)
    contact_no = request.form.get('contact_no', None)
    email_id = request.form.get('email_id', None)
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO customer_details (name, dob, gender, country, state, city, contact_no, email_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, dob, gender, country, state, city, contact_no, email_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    model_id = int(request.form['model_id'])
    customer_id = int(request.form['customer_id'])
    quantity = int(request.form['quantity'])
    date = request.form['date']
    
    # Get mobile price
    conn = get_db_connection()
    mobile = conn.execute('SELECT price FROM mobile_details WHERE model_id = ?', (model_id,)).fetchone()
    total_amount = mobile['price'] * quantity
    
    # Insert transaction
    conn.execute('''
        INSERT INTO transaction_details (model_id, customer_id, quantity, date, total_amount)
        VALUES (?, ?, ?, ?, ?)
    ''', (model_id, customer_id, quantity, date, total_amount))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/delete_transaction/<int:tr_id>')
def delete_transaction(tr_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM transaction_details WHERE tr_id = ?', (tr_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/edit_transaction/<int:tr_id>', methods=['GET', 'POST'])
def edit_transaction(tr_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        model_id = int(request.form['model_id'])
        customer_id = int(request.form['customer_id'])
        quantity = int(request.form['quantity'])
        date = request.form['date']
        
        # Get mobile price
        mobile = conn.execute('SELECT price FROM mobile_details WHERE model_id = ?', (model_id,)).fetchone()
        total_amount = mobile['price'] * quantity
        
        # Update transaction
        conn.execute('''
            UPDATE transaction_details 
            SET model_id = ?, customer_id = ?, quantity = ?, date = ?, total_amount = ?
            WHERE tr_id = ?
        ''', (model_id, customer_id, quantity, date, total_amount, tr_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    # GET request - show edit form
    transaction = conn.execute('''
        SELECT td.*, md.brand_name, md.model_name, cd.name as customer_name
        FROM transaction_details td
        JOIN mobile_details md ON td.model_id = md.model_id
        JOIN customer_details cd ON td.customer_id = cd.customer_id
        WHERE td.tr_id = ?
    ''', (tr_id,)).fetchone()
    
    models = conn.execute('SELECT model_id, brand_name, model_name FROM mobile_details').fetchall()
    customers = conn.execute('SELECT customer_id, name FROM customer_details').fetchall()
    conn.close()
    
    return render_template('edit.html', transaction=transaction, models=models, customers=customers)

if __name__ == '__main__':
    app.run(debug=True)