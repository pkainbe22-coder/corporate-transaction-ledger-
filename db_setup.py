import mysql.connector
from config import DB_CONFIG

# Database configuration
def create_database():
    """Create the main database"""
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS ledger_db")
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ Database 'ledger_db' created or already exists")


def create_tables():
    """Create all required tables"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            role ENUM('admin', 'manager', 'user', 'viewer') DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            is_active BOOLEAN DEFAULT TRUE,
            INDEX idx_username (username),
            INDEX idx_email (email)
        )
    """)
    print("✓ Table 'users' created")
    
    # Ledger Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            transaction_id VARCHAR(255) NOT NULL UNIQUE,
            budgetary_amount DECIMAL(15,2),
            marks VARCHAR(255),
            from_account VARCHAR(255) NOT NULL,
            to_receiver_code VARCHAR(255) NOT NULL,
            amount DECIMAL(15,2) NOT NULL,
            ifsc_code VARCHAR(11),
            transaction_status ENUM('pending', 'success', 'failed', 'cancelled', 'on_hold') NOT NULL,
            inserted_by VARCHAR(255) NOT NULL,
            hash VARCHAR(64) NOT NULL,
            previous_hash VARCHAR(64),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT FALSE,
            INDEX idx_transaction_id (transaction_id),
            INDEX idx_date (date),
            INDEX idx_status (transaction_status),
            INDEX idx_hash (hash)
        )
    """)
    print("✓ Table 'ledger' created")
    
    # Audit Log Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            action VARCHAR(100) NOT NULL,
            details TEXT,
            ip_address VARCHAR(45),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_action (action),
            INDEX idx_timestamp (timestamp),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✓ Table 'audit_log' created")
    
    # Transaction Reports Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            report_name VARCHAR(255) NOT NULL,
            report_type VARCHAR(50) NOT NULL,
            created_by INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            start_date DATE,
            end_date DATE,
            total_amount DECIMAL(15,2),
            transaction_count INT,
            report_data LONGTEXT,
            file_path VARCHAR(255),
            INDEX idx_created_by (created_by),
            INDEX idx_created_at (created_at),
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✓ Table 'transaction_reports' created")
    
    # System Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            setting_key VARCHAR(255) UNIQUE NOT NULL,
            setting_value LONGTEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_setting_key (setting_key)
        )
    """)
    print("✓ Table 'system_settings' created")
    
    conn.commit()
    cursor.close()
    conn.close()


def insert_default_data():
    """Insert default system settings and admin user"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Check if admin user already exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash('Admin@123', method='scrypt')
            cursor.execute("""
                INSERT INTO users (username, password, email, role, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, ('admin', hashed_password, 'admin@ledger.local', 'admin', True))
            print("✓ Default admin user created (username: admin, password: Admin@123)")
        
        # Insert default settings
        cursor.execute("SELECT COUNT(*) FROM system_settings")
        if cursor.fetchone()[0] == 0:
            settings = [
                ('company_name', 'Corporate Transaction Ledger System', 'Company name displayed in application'),
                ('max_transaction_amount', '999999999.99', 'Maximum allowed transaction amount'),
                ('blockchain_enabled', 'true', 'Enable blockchain verification'),
                ('audit_logging_enabled', 'true', 'Enable audit logging'),
                ('report_export_enabled', 'true', 'Enable report export functionality'),
            ]
            
            for key, value, desc in settings:
                cursor.execute("""
                    INSERT INTO system_settings (setting_key, setting_value, description)
                    VALUES (%s, %s, %s)
                """, (key, value, desc))
            
            print("✓ Default system settings created")
        
        conn.commit()
    except mysql.connector.IntegrityError:
        pass
    finally:
        cursor.close()
        conn.close()


def create_indexes():
    """Create additional performance indexes"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    indexes = [
        ("ALTER TABLE ledger ADD INDEX idx_from_account (from_account)"),
        ("ALTER TABLE ledger ADD INDEX idx_to_receiver (to_receiver_code)"),
        ("ALTER TABLE audit_log ADD INDEX idx_combined (user_id, timestamp)"),
    ]
    
    for index_query in indexes:
        try:
            cursor.execute(index_query)
        except mysql.connector.Error as e:
            if "Duplicate key name" not in str(e):
                print(f"Note: {index_query} - {str(e)}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ Performance indexes created")


def main():
    """Main function to set up database"""
    print("\n" + "="*60)
    print("   Corporate Transaction Ledger System")
    print("   Database Setup")
    print("="*60 + "\n")
    
    try:
        print("Creating database...")
        create_database()
        
        print("\nCreating tables...")
        create_tables()
        
        print("\nInserting default data...")
        insert_default_data()
        
        print("\nCreating indexes...")
        create_indexes()
        
        print("\n" + "="*60)
        print("✓ Database setup completed successfully!")
        print("="*60 + "\n")
        
    except mysql.connector.Error as err:
        if err.errno == 2003:
            print(f"\n✗ Error: Cannot connect to MySQL server")
            print(f"   Please ensure MySQL is running and credentials in config.py are correct")
        else:
            print(f"\n✗ Database Error: {err}")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    main()