import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime
from blockchain import create_blockchain_entry
from config import DB_CONFIG
from utils import (
    validate_email, validate_password, validate_amount, 
    log_audit_action, get_client_ip, require_admin, require_role,
    format_currency, format_date, generate_transaction_report
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configure logging
logging.basicConfig(filename='ledger.log', level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, email, role='user'):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, role FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['email'], user_data['role'])
        return None
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

# ===== AUTHENTICATION ROUTES =====

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validation
        if not all([username, email, password, password_confirm]):
            flash('All fields are required!', 'error')
            return render_template('register.html')
        
        if password != password_confirm:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if not validate_email(email):
            flash('Invalid email format!', 'error')
            return render_template('register.html')
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'error')
            return render_template('register.html')
        
        # Hash password
        hashed_password = generate_password_hash(password, method='scrypt')
        
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
                (username, hashed_password, email, 'user')
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"New user registered: {username}")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except mysql.connector.IntegrityError:
            flash('Username or email already exists!', 'error')
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password required!', 'error')
            return render_template('login.html')
        
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, email, password, role FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            cursor.close()
            
            if user_data and check_password_hash(user_data['password'], password):
                user = User(user_data['id'], user_data['username'], user_data['email'], user_data['role'])
                login_user(user)
                
                # Update last login
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user_data['id'],))
                conn.commit()
                
                logger.info(f"User logged in: {username}")
                log_audit_action(user_data['id'], 'LOGIN', f'User {username} logged in', get_client_ip(request))
                
                flash(f'Welcome, {username}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password!', 'error')
                logger.warning(f"Failed login attempt for: {username}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f"User logged out: {current_user.username}")
    log_audit_action(current_user.id, 'LOGOUT', f'User {current_user.username} logged out', get_client_ip(request))
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# ===== MAIN ROUTES =====

@app.route('/')
@login_required
def index():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get recent transactions
        cursor.execute("""
            SELECT id, date, transaction_id, amount, from_account, to_receiver_code, 
                   transaction_status, inserted_by, created_at
            FROM ledger 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_transactions = cursor.fetchall()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as total FROM ledger")
        total_txns = cursor.fetchone()['total']
        
        cursor.execute("SELECT SUM(amount) as total_amount FROM ledger")
        total_amount = cursor.fetchone()['total_amount'] or 0
        
        cursor.execute("SELECT COUNT(*) as count FROM ledger WHERE transaction_status = 'success'")
        success_count = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return render_template('index.html', 
                             recent_transactions=recent_transactions,
                             total_transactions=total_txns,
                             total_amount=format_currency(total_amount),
                             successful_transactions=success_count)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('Error loading dashboard!', 'error')
        return render_template('index.html')

@app.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM ledger")
        total = cursor.fetchone()['count']
        
        # Get paginated transactions
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT id, date, transaction_id, amount, from_account, to_receiver_code,
                   transaction_status, inserted_by, created_at
            FROM ledger
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        transactions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('transactions.html',
                             transactions=transactions,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    except Exception as e:
        logger.error(f"Transactions error: {str(e)}")
        flash('Error loading transactions!', 'error')
        return render_template('transactions.html', transactions=[])

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            # Get form data
            date = request.form.get('date', '')
            transaction_id = request.form.get('transaction_id', '').strip().upper()
            budgetary_amount = request.form.get('budgetary_amount', '0')
            marks = request.form.get('marks', '').strip()
            from_account = request.form.get('from_account', '').strip()
            to_receiver_code = request.form.get('to_receiver_code', '').strip()
            amount = request.form.get('amount', '0')
            ifsc_code = request.form.get('ifsc_code', '').strip().upper()
            transaction_status = request.form.get('transaction_status', 'pending')
            
            # Validation
            if not all([date, transaction_id, from_account, to_receiver_code, amount]):
                flash('All required fields must be filled!', 'error')
                return render_template('add_transaction.html')
            
            if not validate_amount(amount):
                flash('Invalid amount!', 'error')
                return render_template('add_transaction.html')
            
            # Create blockchain entry
            hash_value, previous_hash = create_blockchain_entry(
                date, transaction_id, budgetary_amount, marks,
                from_account, to_receiver_code, amount, ifsc_code,
                transaction_status, current_user.username
            )
            
            # Insert into database
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ledger 
                (date, transaction_id, budgetary_amount, marks, from_account, to_receiver_code, 
                 amount, ifsc_code, transaction_status, inserted_by, hash, previous_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (date, transaction_id, budgetary_amount, marks, from_account, to_receiver_code,
                   amount, ifsc_code, transaction_status, current_user.username, hash_value, previous_hash))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Transaction added by {current_user.username}: ID {transaction_id}")
            log_audit_action(current_user.id, 'ADD_TRANSACTION', 
                           f'Transaction {transaction_id} added for amount {amount}',
                           get_client_ip(request))
            
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('transactions'))
            
        except mysql.connector.IntegrityError:
            flash('Transaction ID already exists!', 'error')
        except Exception as e:
            logger.error(f"Add transaction error: {str(e)}")
            flash('Error adding transaction!', 'error')
    
    return render_template('add_transaction.html')

@app.route('/transaction/<int:txn_id>')
@login_required
def view_transaction(txn_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ledger WHERE id = %s", (txn_id,))
        transaction = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not transaction:
            flash('Transaction not found!', 'error')
            return redirect(url_for('transactions'))
        
        return render_template('transaction_detail.html', transaction=transaction)
    except Exception as e:
        logger.error(f"View transaction error: {str(e)}")
        flash('Error loading transaction!', 'error')
        return redirect(url_for('transactions'))

@app.route('/reports')
@login_required
@require_role('admin', 'manager')
def reports():
    try:
        report_type = request.args.get('type', 'summary')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Build query
        query = "SELECT * FROM ledger WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        
        # Generate report
        report = generate_transaction_report(transactions, report_type)
        
        cursor.close()
        conn.close()
        
        return render_template('reports.html', report=report, report_type=report_type)
    except Exception as e:
        logger.error(f"Reports error: {str(e)}")
        flash('Error generating report!', 'error')
        return render_template('reports.html')

@app.route('/audit-log')
@login_required
@require_admin
def audit_log():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 25
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM audit_log")
        total = cursor.fetchone()['count']
        
        # Get paginated logs
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT al.*, u.username
            FROM audit_log al
            JOIN users u ON al.user_id = u.id
            ORDER BY al.timestamp DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('audit_log.html',
                             logs=logs,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    except Exception as e:
        logger.error(f"Audit log error: {str(e)}")
        flash('Error loading audit log!', 'error')
        return render_template('audit_log.html', logs=[])

# ===== ADMIN ROUTES =====

@app.route('/admin/dashboard')
@login_required
@require_admin
def admin_dashboard():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM ledger")
        total_transactions = cursor.fetchone()['count']
        
        cursor.execute("SELECT SUM(amount) as total FROM ledger")
        total_amount = cursor.fetchone()['total'] or 0
        
        cursor.execute("""
            SELECT transaction_status, COUNT(*) as count
            FROM ledger
            GROUP BY transaction_status
        """)
        status_breakdown = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             total_transactions=total_transactions,
                             total_amount=format_currency(total_amount),
                             status_breakdown=status_breakdown)
    except Exception as e:
        logger.error(f"Admin dashboard error: {str(e)}")
        flash('Error loading admin dashboard!', 'error')
        return render_template('admin/dashboard.html')

@app.route('/admin/users')
@login_required
@require_admin
def manage_users():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, role, created_at, last_login FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin/users.html', users=users)
    except Exception as e:
        logger.error(f"Manage users error: {str(e)}")
        flash('Error loading users!', 'error')
        return render_template('admin/users.html', users=[])

# ===== API ROUTES =====

@app.route('/api/transactions')
@login_required
def api_transactions():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ledger ORDER BY created_at DESC LIMIT 100")
        transactions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(transactions)
    except Exception as e:
        logger.error(f"API transactions error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
@login_required
def api_statistics():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as total FROM ledger")
        total_txns = cursor.fetchone()['total']
        
        cursor.execute("SELECT SUM(amount) as total FROM ledger")
        total_amount = cursor.fetchone()['total'] or 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_transactions': total_txns,
            'total_amount': float(total_amount)
        })
    except Exception as e:
        logger.error(f"API statistics error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
