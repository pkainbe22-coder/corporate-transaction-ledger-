# 🔐 Corporate Transaction Ledger System

A secure, enterprise-grade financial transaction ledger system with blockchain protection, audit logging, and advanced reporting capabilities. Built with Python Flask, MySQL, and SHA-256 cryptography.

## ✨ Key Features

- **🔗 Blockchain Protection** - SHA-256 hashing with chain verification
- **📝 Immutable Records** - Append-only ledger, no modifications allowed
- **🔐 Secure Authentication** - Password hashing and session management
- **📊 Transaction Management** - Complete lifecycle tracking
- **🔍 Audit Logging** - Comprehensive activity tracking
- **📈 Advanced Reports** - Financial analytics and exports
- **👥 Role-Based Access** - Admin, Manager, User, Viewer roles
- **✅ Data Validation** - Comprehensive input validation
- **📱 Responsive UI** - Modern web interface
- **📤 Export Features** - CSV, JSON, PDF export

## 🛠️ Technology Stack

| Component | Technology |
|-----------|----------|
| **Backend** | Python 3.8+ with Flask 2.3.3 |
| **Database** | MySQL 8.0+ |
| **Authentication** | Flask-Login with Werkzeug |
| **Security** | SHA-256 Blockchain |
| **Frontend** | HTML5, Bootstrap, JavaScript |
| **Configuration** | Python-dotenv |

## 📦 Prerequisites

- Python 3.8 or higher
- MySQL Server 8.0 or higher
- pip (Python package manager)
- Git

## 🚀 Quick Start Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/pkainbe22-coder/corporate-transaction-ledger-.git
cd corporate-transaction-ledger-
```

### 2️⃣ Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment
```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your settings
# Update database credentials:
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=your_password
# DB_NAME=ledger_db
```

### 5️⃣ Initialize Database
```bash
python db_setup.py
```

Expected output:
```
============================================================
   Corporate Transaction Ledger System
   Database Setup
============================================================

✓ Database 'ledger_db' created or already exists
✓ Table 'users' created
✓ Table 'ledger' created
✓ Table 'audit_log' created
✓ Table 'transaction_reports' created
✓ Table 'system_settings' created
✓ Default admin user created (username: admin, password: Admin@123)
✓ Performance indexes created

============================================================
✓ Database setup completed successfully!
============================================================
```

### 6️⃣ Run the Application
```bash
python app.py
```

Open your browser: **http://127.0.0.1:5000/**

## 🔑 Default Credentials

| Field | Value |
|-------|-------|
| **Username** | admin |
| **Password** | Admin@123 |
| **Role** | Administrator |

⚠️ **IMPORTANT**: Change the admin password immediately in production!

## 📁 Project Structure

```
corporate-transaction-ledger/
├── app.py                    # Main Flask application
├── blockchain.py             # Blockchain hashing logic
├── db_setup.py              # Database initialization
├── config.py                # Configuration management
├── utils.py                 # Utility functions
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── README.md                # Documentation (this file)
├── ledger.log               # Application logs
└── templates/               # HTML templates
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── add_transaction.html
    ├── transactions.html
    ├── reports.html
    └── audit_log.html
```

## 🔗 API Endpoints

### Authentication Routes
```
POST   /register              - User registration
GET    /register              - Registration page
POST   /login                 - User login
GET    /login                 - Login page
GET    /logout                - User logout
```

### Main Routes
```
GET    /                      - Dashboard
POST   /add                   - Add transaction
GET    /transactions          - View all transactions
GET    /transaction/<id>      - View transaction details
GET    /reports               - Generate reports
GET    /audit-log             - View audit logs
```

### Admin Routes
```
GET    /admin/dashboard       - Admin statistics
GET    /admin/users           - User management
GET    /admin/settings        - System settings
POST   /admin/users/<id>/role - Update user role
```

### JSON API
```
GET    /api/transactions      - Get transactions (JSON)
GET    /api/statistics        - System statistics
GET    /api/reports           - Export reports
GET    /api/audit-log         - Audit log data
```

## 👥 User Roles & Permissions

| Permission | Admin | Manager | User | Viewer |
|-----------|:-----:|:-------:|:----:|:------:|
| Create Transactions | ✅ | ✅ | ✅ | ❌ |
| View Transactions | ✅ | ✅ | ✅ | ✅ |
| Export Data | ✅ | ✅ | ❌ | ❌ |
| Manage Users | ✅ | ❌ | ❌ | ❌ |
| View Audit Log | ✅ | ✅ | ❌ | ❌ |

## 💾 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role ENUM('admin', 'manager', 'user', 'viewer') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Ledger Table
```sql
CREATE TABLE ledger (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date DATE NOT NULL,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    budgetary_amount DECIMAL(15,2),
    marks VARCHAR(255),
    from_account VARCHAR(255) NOT NULL,
    to_receiver_code VARCHAR(255) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    ifsc_code VARCHAR(11),
    transaction_status ENUM('pending', 'success', 'failed', 'cancelled', 'on_hold'),
    inserted_by VARCHAR(255) NOT NULL,
    hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE
);
```

### Audit Log Table
```sql
CREATE TABLE audit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Database
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'ledger_db'
}

# Security
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_UPPERCASE = True

# Features
ENABLE_AUDIT_LOG = True
ENABLE_REPORTS = True
ENABLE_EXPORT = True
ENABLE_ROLE_BASED_ACCESS = True
```

## 🔒 Security Features

✅ **Password Security**
- SHA-256 hashing with salt
- Strong password enforcement
- Session expiration

✅ **Data Protection**
- Blockchain-protected records
- Immutable ledger entries
- Comprehensive audit trails

✅ **Access Control**
- Role-based permissions
- Session management
- IP address tracking

✅ **Input Security**
- SQL injection prevention
- XSS protection
- Input sanitization

## 🛠️ Utility Functions

The `utils.py` module provides:

```python
# Validation Functions
validate_email(email)
validate_password(password)
validate_amount(amount)
validate_ifsc_code(ifsc_code)
validate_transaction_id(transaction_id)

# Formatting Functions
format_currency(amount)
format_date(date_obj)

# Audit & Logging
log_audit_action(user_id, action, details, ip_address)

# Data Export
export_to_csv(data)
export_to_json(data)

# Access Control
@require_admin
@require_role('admin', 'manager')

# Blockchain
check_blockchain_integrity(entries)
```

## 📊 Reporting

### Available Reports
- Daily Summary Report
- Weekly Summary Report
- Monthly Summary Report
- Transaction Detail Report
- Account-wise Report
- Status-wise Report

### Export Formats
- CSV
- JSON
- PDF (coming soon)

## 🐛 Troubleshooting

### MySQL Connection Error
```
Error: Cannot connect to MySQL server
Solution:
1. Ensure MySQL service is running
2. Check DB credentials in .env
3. Verify user has database privileges
```

### Port Already in Use
```
Error: Address already in use
Solution:
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or change port in app.py
app.run(port=5001)
```

### Import Errors
```
Solution:
pip install -r requirements.txt --force-reinstall
```

### Database Setup Issues
```
# Check database connection
mysql -h localhost -u root -p

# Run setup again
python db_setup.py
```

## 📝 Logging

Application logs are saved to `ledger.log`:

```bash
# View all logs
tail -f ledger.log

# View errors only
grep "ERROR" ledger.log

# View specific user activity
grep "user_id" ledger.log

# Search by date
grep "2026-05-29" ledger.log
```

## 🚀 Performance Tips

1. **Database Indexing** - Already optimized with performance indexes
2. **Connection Pooling** - MySQL connector manages connections
3. **Pagination** - Ledger views use pagination by default
4. **Caching** - Static assets are cached
5. **Query Optimization** - Efficient SQL queries

## 📈 Advanced Features

### Blockchain Verification
```python
from utils import check_blockchain_integrity
is_valid = check_blockchain_integrity(ledger_entries)
```

### Audit Trail
```python
from utils import log_audit_action
log_audit_action(user_id, 'ADD_TRANSACTION', 'Details', ip_address)
```

### Role-Based Access
```python
from utils import require_admin, require_role

@app.route('/admin')
@require_admin
def admin_panel():
    return render_template('admin/dashboard.html')
```

## 🔄 Development Workflow

### Setup Development Environment
```bash
export FLASK_ENV=development
pip install -r requirements.txt
```

### Run Tests
```bash
python -m pytest tests/
```

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Comment complex logic

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📋 Roadmap

- [ ] Multi-factor Authentication (2FA)
- [ ] REST API with JWT tokens
- [ ] Advanced analytics dashboard
- [ ] Data encryption at rest
- [ ] Distributed ledger support
- [ ] Mobile application
- [ ] Real-time notifications
- [ ] Automated backups
- [ ] Docker containerization
- [ ] Kubernetes deployment

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 📞 Support & Contact

- 📧 **Email**: pkain_be22@thapar.edu
- 🐛 **Issues**: Open an issue on GitHub
- 💬 **Discussions**: Use GitHub Discussions

## 👤 Author

**pkainbe22-coder**
- GitHub: [@pkainbe22-coder](https://github.com/pkainbe22-coder)
- Email: pkain_be22@thapar.edu

## 📅 Changelog

### Version 2.0 (Current)
- ✨ Role-based access control
- ✨ Audit logging system
- ✨ Transaction reports & export
- ✨ Enhanced database schema
- ✨ Improved security validation
- ✨ Utility functions library
- ✨ Configuration management
- 🐛 Security improvements
- 📈 Performance optimizations

### Version 1.0 (Base)
- Basic ledger functionality
- Blockchain protection
- User authentication

---

**Last Updated**: May 29, 2026
**Version**: 2.0.0
**Status**: Active Development ✅

**Made with ❤️ by [@pkainbe22-coder](https://github.com/pkainbe22-coder)**