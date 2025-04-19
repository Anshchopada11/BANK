from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)  # Simplified initialization (no need for template_folder)

app.secret_key = 'your_secret_key_here'

# Create DB if not exists
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance REAL DEFAULT 1000.0
            )
        ''')
        conn.commit()
        conn.close()

init_db()

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_money', methods=['GET', 'POST'])
def add_money():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        username = session['user']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('UPDATE users SET balance = balance + ? WHERE username = ?', (amount, username))
        conn.commit()
        conn.close()
        flash('Money added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_money.html')


@app.route('/send_money', methods=['GET', 'POST'])
def send_money():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        sender = session['user']
        recipient = request.form['recipient']
        amount = float(request.form['amount'])

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get sender balance
        c.execute('SELECT balance FROM users WHERE username=?', (sender,))
        sender_balance = c.fetchone()

        if not sender_balance or sender_balance[0] < amount:
            flash('Insufficient balance or sender not found.', 'danger')
            conn.close()
            return redirect(url_for('send_money'))

        # Check if recipient exists
        c.execute('SELECT * FROM users WHERE username=?', (recipient,))
        if not c.fetchone():
            flash('Recipient not found.', 'danger')
            conn.close()
            return redirect(url_for('send_money'))

        # Perform transfer
        c.execute('UPDATE users SET balance = balance - ? WHERE username = ?', (amount, sender))
        c.execute('UPDATE users SET balance = balance + ? WHERE username = ?', (amount, recipient))
        conn.commit()
        conn.close()

        flash(f'Successfully sent ₹{amount} to {recipient}', 'success')
        return redirect(url_for('dashboard'))

    return render_template('send_money.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Username already exists.', 'danger')
        conn.close()
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE username=?', (username,))
    balance = c.fetchone()[0]
    conn.close()
    return render_template('dashboard.html', username=username, balance=balance)

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))

# Run App
if __name__ == '__main__':
    app.run(debug=True)
