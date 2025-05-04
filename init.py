## Author: Abhishek Manoj Sutaria
import sqlite3
import random
from datetime import datetime, timedelta

DATABASE = 'sales.db'

# Creating tables in the database
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
                  email_id TEXT UNIQUE)''')
    
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

# Mobile models are defined for sample data
def generate_mobiles():
    brands = [
        ('Apple', ['iPhone 14', 'iPhone 14 Pro', 'iPhone 13', 'iPhone SE']),
        ('Samsung', ['Galaxy S23', 'Galaxy Z Flip', 'Galaxy A54', 'Galaxy Note']),
        ('Google', ['Pixel 7', 'Pixel 7 Pro', 'Pixel 6a', 'Pixel Fold']),
        ('OnePlus', ['11 5G', 'Nord CE 3', '10 Pro', '9RT 5G']),
        ('Xiaomi', ['13 Pro', '12T Pro', 'Redmi Note 12', 'Mix Fold 2'])
    ]
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    for brand, models in brands:
        for model in models:
            price = random.randint(300, 1500) - 0.01
            c.execute('INSERT INTO mobile_details (brand_name, model_name, price) VALUES (?, ?, ?)',
                     (brand, model, price))
    
    conn.commit()
    conn.close()

# Customers and their details are defined for sample data
def generate_customers():
    customers = [
        ('John Smith', '1990-05-15', 'Male', 'USA', 'CA', 'Los Angeles', '+1 555 0100', 'john@example.com'),
        ('Emma Wilson', '1985-12-08', 'Female', 'UK', None, 'London', '+44 20 7946 0000', 'emma@example.com'),
        ('Raj Patel', '1995-08-22', 'Male', 'India', 'MH', 'Mumbai', '+91 22 2569 0000', 'raj@example.com'),
        ('Linh Nguyen', '2000-03-30', 'Female', 'Vietnam', 'HN', 'Hanoi', '+84 24 3936 0000', 'linh@example.com'),
        ('Maria Garcia', '1988-07-12', 'Female', 'Spain', 'MD', 'Madrid', '+34 915 000 000', 'maria@example.com')
    ]
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    for customer in customers:
        c.execute('''INSERT INTO customer_details 
                    (name, dob, gender, country, state, city, contact_no, email_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', customer)
    
    conn.commit()
    conn.close()

# Sample transactions are generated to test the application
def generate_transactions():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Get all mobile models and customers
    mobiles = c.execute('SELECT model_id, price FROM mobile_details').fetchall()
    customers = c.execute('SELECT customer_id FROM customer_details').fetchall()
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 4, 9)
    
    current_date = start_date
    while current_date <= end_date:
        # Generate 0-5 transactions per day. Number in for loop can be changed to increase number of transactions per day.
        for _ in range(random.randint(0, 5)):
            model_id, price = random.choice(mobiles)
            customer_id = random.choice(customers)[0]
            quantity = random.randint(1, 3)
            total = price * quantity
            
            c.execute('''INSERT INTO transaction_details 
                        (model_id, customer_id, quantity, date, total_amount)
                        VALUES (?, ?, ?, ?, ?)''',
                     (model_id, customer_id, quantity, 
                      current_date.strftime('%Y-%m-%d'), total))
        current_date += timedelta(days=1)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    generate_mobiles()
    generate_customers()
    generate_transactions()
    print("Database initialization completed!")