# Corporate Transaction Ledger System - Utility Functions

import re
import logging
from datetime import datetime
from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user

# Configure logging
logger = logging.getLogger(__name__)


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


def validate_account_number(account_number):
    """Validate account number format"""
    return len(account_number) >= 10 and account_number.isalnum()


def validate_ifsc_code(ifsc_code):
    """Validate IFSC code format (Indian banking)"""
    pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    return re.match(pattern, ifsc_code) is not None


def validate_transaction_id(transaction_id):
    """Validate transaction ID format"""
    pattern = r'^[A-Z0-9]{5,20}$'
    return re.match(pattern, transaction_id) is not None


def validate_amount(amount):
    """Validate transaction amount"""
    try:
        amount_float = float(amount)
        return amount_float > 0 and amount_float < 999999999.99
    except (ValueError, TypeError):
        return False


def validate_date(date_string):
    """Validate date format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def sanitize_input(user_input):
    """Remove potentially harmful characters from user input"""
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    sanitized = user_input
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized.strip()


def format_currency(amount):
    """Format amount as currency"""
    try:
        return f"₹ {float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₹ 0.00"


def format_date(date_obj):
    """Format date object to readable string"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime('%d-%m-%Y') if date_obj else 'N/A'


def get_current_timestamp():
    """Get current timestamp in standard format"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def log_audit_action(user_id, action, details, ip_address=None):
    """
    Log audit action to database
    
    Args:
        user_id: ID of user performing action
        action: Type of action (e.g., 'ADD_TRANSACTION', 'LOGIN', 'EXPORT')
        details: Additional details about the action
        ip_address: IP address of user
    """
    try:
        timestamp = get_current_timestamp()
        logger.info(f"AUDIT - User: {user_id}, Action: {action}, Details: {details}, IP: {ip_address}, Time: {timestamp}")
    except Exception as e:
        logger.error(f"Error logging audit action: {str(e)}")


def get_client_ip(request_obj):
    """Get client IP address from request"""
    if request_obj.headers.get('X-Forwarded-For'):
        return request_obj.headers.get('X-Forwarded-For').split(',')[0]
    return request_obj.remote_addr


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'role'):
            flash('Unauthorized access', 'error')
            return redirect(url_for('login'))
        
        if current_user.role != 'admin':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def require_role(*roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not hasattr(current_user, 'role'):
                flash('Unauthorized access', 'error')
                return redirect(url_for('login'))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def paginate_results(items, page, per_page):
    """Paginate a list of items"""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page,
        'has_next': end < total,
        'has_prev': page > 1
    }


def generate_transaction_report(transactions, report_type='summary'):
    """Generate report from transaction data"""
    if not transactions:
        return {'status': 'error', 'message': 'No transactions to report'}
    
    report = {
        'type': report_type,
        'generated_at': get_current_timestamp(),
        'total_transactions': len(transactions),
        'total_amount': 0,
        'successful_count': 0,
        'failed_count': 0,
        'by_status': {},
        'transactions': transactions
    }
    
    for txn in transactions:
        try:
            report['total_amount'] += float(txn.get('amount', 0))
        except (ValueError, TypeError):
            pass
        
        status = txn.get('transaction_status', 'unknown')
        if status == 'success':
            report['successful_count'] += 1
        elif status == 'failed':
            report['failed_count'] += 1
        
        if status not in report['by_status']:
            report['by_status'][status] = 0
        report['by_status'][status] += 1
    
    return report


def check_blockchain_integrity(ledger_entries):
    """
    Verify blockchain integrity of ledger entries
    
    Returns True if all hashes are correctly chained
    """
    if not ledger_entries:
        return True
    
    for i, entry in enumerate(ledger_entries):
        if i == 0:
            if entry.get('previous_hash') != '0' * 64:
                return False
        else:
            if entry.get('previous_hash') != ledger_entries[i-1].get('hash'):
                return False
    
    return True


def export_to_csv(data, filename=None):
    """Convert data to CSV format"""
    import csv
    from io import StringIO
    
    if not filename:
        filename = f"ledger_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if not data:
        return None
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue(), filename


def export_to_json(data, filename=None):
    """Convert data to JSON format"""
    import json
    
    if not filename:
        filename = f"ledger_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return json.dumps(data, indent=2, default=str), filename