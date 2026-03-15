from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
import os
from datetime import datetime, timezone, timedelta

PKT = timezone(timedelta(hours=5))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'))

@app.template_filter('pkt')
def to_pkt(dt_str, fmt='%Y-%m-%d %H:%M'):
    """Convert a UTC datetime string to PKT (GMT+5)."""
    if not dt_str:
        return ''
    try:
        dt = datetime.fromisoformat(str(dt_str)).replace(tzinfo=timezone.utc)
        return dt.astimezone(PKT).strftime(fmt)
    except Exception:
        return str(dt_str)[:16]
app.secret_key = 'pos_secret_key_2024'
DB_PATH = os.path.join(BASE_DIR, 'pos.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT '',
            price REAL NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            unit TEXT DEFAULT 'pcs',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            customer_name TEXT DEFAULT 'Walk-in',
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            total REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            sale_id INTEGER,
            amount REAL NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT DEFAULT '',
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (sale_id) REFERENCES sales(id)
        );
    ''')
    conn.commit()
    conn.close()


# ─── HOME ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('pos'))


# ─── INVENTORY ───────────────────────────────────────────────────────────────
@app.route('/inventory')
def inventory():
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY name').fetchall()
    conn.close()
    return render_template('inventory.html', products=products)


@app.route('/inventory/add', methods=['POST'])
def add_product():
    name = request.form['name'].strip()
    category = request.form.get('category', '').strip()
    price = float(request.form['price'])
    quantity = float(request.form['quantity'])
    unit = request.form.get('unit', 'pcs').strip()
    conn = get_db()
    conn.execute(
        'INSERT INTO products (name, category, price, quantity, unit) VALUES (?, ?, ?, ?, ?)',
        (name, category, price, quantity, unit)
    )
    conn.commit()
    conn.close()
    flash('Product added successfully!', 'success')
    return redirect(url_for('inventory'))


@app.route('/inventory/edit/<int:pid>', methods=['POST'])
def edit_product(pid):
    name = request.form['name'].strip()
    category = request.form.get('category', '').strip()
    price = float(request.form['price'])
    quantity = float(request.form['quantity'])
    unit = request.form.get('unit', 'pcs').strip()
    conn = get_db()
    conn.execute(
        'UPDATE products SET name=?, category=?, price=?, quantity=?, unit=? WHERE id=?',
        (name, category, price, quantity, unit, pid)
    )
    conn.commit()
    conn.close()
    flash('Product updated!', 'success')
    return redirect(url_for('inventory'))


@app.route('/inventory/delete/<int:pid>', methods=['POST'])
def delete_product(pid):
    conn = get_db()
    conn.execute('DELETE FROM products WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    flash('Product deleted.', 'info')
    return redirect(url_for('inventory'))


# ─── CUSTOMERS ───────────────────────────────────────────────────────────────
@app.route('/customers')
def customers():
    conn = get_db()
    custs = conn.execute('SELECT * FROM customers ORDER BY name').fetchall()
    conn.close()
    return render_template('customers.html', customers=custs)


@app.route('/customers/add', methods=['POST'])
def add_customer():
    name = request.form['name'].strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    conn = get_db()
    conn.execute(
        'INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)',
        (name, phone, address)
    )
    conn.commit()
    conn.close()
    flash('Customer added!', 'success')
    return redirect(url_for('customers'))


@app.route('/customers/edit/<int:cid>', methods=['POST'])
def edit_customer(cid):
    name = request.form['name'].strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    conn = get_db()
    conn.execute(
        'UPDATE customers SET name=?, phone=?, address=? WHERE id=?',
        (name, phone, address, cid)
    )
    conn.commit()
    conn.close()
    flash('Customer updated!', 'success')
    return redirect(url_for('customers'))


@app.route('/customers/delete/<int:cid>', methods=['POST'])
def delete_customer(cid):
    conn = get_db()
    conn.execute('DELETE FROM customers WHERE id=?', (cid,))
    conn.commit()
    conn.close()
    flash('Customer deleted.', 'info')
    return redirect(url_for('customers'))


# ─── POS ─────────────────────────────────────────────────────────────────────
@app.route('/pos')
def pos():
    conn = get_db()
    products = conn.execute('SELECT * FROM products WHERE quantity > 0 ORDER BY name').fetchall()
    custs = conn.execute('SELECT * FROM customers ORDER BY name').fetchall()
    conn.close()
    return render_template('pos.html', products=products, customers=custs)


@app.route('/pos/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    customer_id = data.get('customer_id') or None
    customer_name = data.get('customer_name', 'Walk-in')
    items = data.get('items', [])
    discount = float(data.get('discount', 0))
    paid_amount = float(data.get('paid_amount', 0))
    notes = data.get('notes', '')

    if not items:
        return jsonify({'success': False, 'error': 'No items in cart'})

    subtotal = sum(float(i['quantity']) * float(i['price']) for i in items)
    total = max(0, subtotal - discount)
    balance = max(0, total - paid_amount)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO sales
               (customer_id, customer_name, subtotal, discount, total, paid_amount, balance, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (customer_id, customer_name, subtotal, discount, total, paid_amount, balance, notes)
        )
        sale_id = cur.lastrowid

        for item in items:
            qty = float(item['quantity'])
            price = float(item['price'])
            cur.execute(
                '''INSERT INTO sale_items
                   (sale_id, product_id, product_name, quantity, unit_price, line_total)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (sale_id, item['product_id'], item['name'], qty, price, qty * price)
            )
            cur.execute(
                'UPDATE products SET quantity = quantity - ? WHERE id = ?',
                (qty, item['product_id'])
            )

        if paid_amount > 0 and customer_id:
            cur.execute(
                'INSERT INTO payments (customer_id, sale_id, amount, notes) VALUES (?, ?, ?, ?)',
                (customer_id, sale_id, paid_amount, 'Payment at sale')
            )

        conn.commit()
        return jsonify({'success': True, 'sale_id': sale_id, 'balance': balance, 'total': total})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()


@app.route('/pos/receipt/<int:sale_id>')
def receipt(sale_id):
    conn = get_db()
    sale = conn.execute('SELECT * FROM sales WHERE id=?', (sale_id,)).fetchone()
    items = conn.execute('SELECT * FROM sale_items WHERE sale_id=?', (sale_id,)).fetchall()
    conn.close()
    if not sale:
        return redirect(url_for('pos'))
    return render_template('receipt.html', sale=sale, items=items)


@app.route('/api/products')
def api_products():
    q = request.args.get('q', '')
    conn = get_db()
    if q:
        prods = conn.execute(
            "SELECT * FROM products WHERE name LIKE ? AND quantity > 0 ORDER BY name",
            (f'%{q}%',)
        ).fetchall()
    else:
        prods = conn.execute(
            'SELECT * FROM products WHERE quantity > 0 ORDER BY name'
        ).fetchall()
    conn.close()
    return jsonify([dict(p) for p in prods])


# ─── CASH LEDGER ─────────────────────────────────────────────────────────────
@app.route('/ledger')
def ledger():
    conn = get_db()
    outstanding = conn.execute('''
        SELECT c.id, c.name, c.phone,
               SUM(s.balance) as total_balance,
               COUNT(s.id) as sale_count
        FROM customers c
        JOIN sales s ON s.customer_id = c.id
        WHERE s.balance > 0
        GROUP BY c.id, c.name, c.phone
        ORDER BY total_balance DESC
    ''').fetchall()

    recent_payments = conn.execute('''
        SELECT p.*, c.name as customer_name
        FROM payments p
        JOIN customers c ON c.id = p.customer_id
        ORDER BY p.payment_date DESC
        LIMIT 20
    ''').fetchall()

    custs = conn.execute('SELECT * FROM customers ORDER BY name').fetchall()
    conn.close()
    return render_template('ledger.html', outstanding=outstanding,
                           recent_payments=recent_payments, customers=custs)


@app.route('/ledger/customer/<int:cid>')
def customer_ledger(cid):
    conn = get_db()
    customer = conn.execute('SELECT * FROM customers WHERE id=?', (cid,)).fetchone()
    sales = conn.execute(
        'SELECT * FROM sales WHERE customer_id=? ORDER BY sale_date DESC', (cid,)
    ).fetchall()
    payments = conn.execute(
        'SELECT * FROM payments WHERE customer_id=? ORDER BY payment_date DESC', (cid,)
    ).fetchall()
    total_balance = conn.execute(
        'SELECT COALESCE(SUM(balance), 0) as total FROM sales WHERE customer_id=?', (cid,)
    ).fetchone()['total']
    conn.close()
    if not customer:
        return redirect(url_for('ledger'))
    return render_template('customer_ledger.html', customer=customer,
                           sales=sales, payments=payments, total_balance=total_balance)


@app.route('/ledger/pay', methods=['POST'])
def record_payment():
    customer_id = int(request.form['customer_id'])
    sale_id = request.form.get('sale_id') or None
    amount = float(request.form['amount'])
    notes = request.form.get('notes', '').strip()

    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO payments (customer_id, sale_id, amount, notes) VALUES (?, ?, ?, ?)',
            (customer_id, sale_id, amount, notes)
        )

        if sale_id:
            conn.execute(
                'UPDATE sales SET balance = MAX(0, balance - ?), paid_amount = paid_amount + ? WHERE id = ?',
                (amount, amount, sale_id)
            )
        else:
            unpaid = conn.execute(
                'SELECT id, balance FROM sales WHERE customer_id=? AND balance > 0 ORDER BY sale_date ASC',
                (customer_id,)
            ).fetchall()
            remaining = amount
            for sale in unpaid:
                if remaining <= 0:
                    break
                apply = min(remaining, sale['balance'])
                conn.execute(
                    'UPDATE sales SET balance = balance - ?, paid_amount = paid_amount + ? WHERE id = ?',
                    (apply, apply, sale['id'])
                )
                remaining -= apply

        conn.commit()
        flash(f'Payment of {amount:,.2f} recorded successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error recording payment: {e}', 'danger')
    finally:
        conn.close()

    redirect_to = request.form.get('redirect_to', 'ledger')
    if redirect_to == 'customer' and customer_id:
        return redirect(url_for('customer_ledger', cid=customer_id))
    return redirect(url_for('ledger'))


if __name__ == '__main__':
    init_db()
    print("=" * 55)
    print("  POS System is running!")
    print("  Open your browser at:  http://localhost:5000")
    print("  Press Ctrl+C to stop.")
    print("=" * 55)
    app.run(debug=False, host='0.0.0.0', port=5000)
