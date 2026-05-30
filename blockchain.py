import hashlib
import mysql.connector
from config import DB_CONFIG
import logging

logger = logging.getLogger(__name__)

def get_previous_hash():
    """
    Get the hash of the most recent transaction
    Returns genesis hash if no transactions exist
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT hash FROM ledger ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return result[0]
        return '0' * 64  # Genesis hash
    except Exception as e:
        logger.error(f"Error getting previous hash: {str(e)}")
        return '0' * 64

def calculate_hash(data):
    """
    Calculate SHA-256 hash of the data
    
    Args:
        data (str): Data to hash
    
    Returns:
        str: SHA-256 hash in hexadecimal format
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def create_blockchain_entry(
    date, transaction_id, budgetary_amount, marks,
    from_account, to_receiver_code, amount, ifsc_code,
    transaction_status, inserted_by
):
    """
    Create a blockchain entry for a transaction
    
    Args:
        date (str): Transaction date
        transaction_id (str): Unique transaction ID
        budgetary_amount (float): Budgetary amount
        marks (str): Additional marks/notes
        from_account (str): Source account
        to_receiver_code (str): Destination receiver code
        amount (float): Transaction amount
        ifsc_code (str): IFSC code
        transaction_status (str): Transaction status
        inserted_by (str): User who inserted the transaction
    
    Returns:
        tuple: (hash_value, previous_hash)
    """
    try:
        # Get previous hash
        previous_hash = get_previous_hash()
        
        # Create data string for hashing
        data = (
            f"{date}{transaction_id}{budgetary_amount}{marks}"
            f"{from_account}{to_receiver_code}{amount}{ifsc_code}"
            f"{transaction_status}{inserted_by}{previous_hash}"
        )
        
        # Calculate hash
        hash_value = calculate_hash(data)
        
        logger.info(f"Blockchain entry created: {transaction_id}")
        
        return hash_value, previous_hash
    
    except Exception as e:
        logger.error(f"Error creating blockchain entry: {str(e)}")
        raise

def verify_blockchain_integrity(ledger_entries):
    """
    Verify the integrity of the blockchain
    
    Args:
        ledger_entries (list): List of ledger entries with hash and previous_hash
    
    Returns:
        bool: True if blockchain is intact, False otherwise
    """
    try:
        if not ledger_entries:
            return True
        
        # Check first entry (genesis block)
        if ledger_entries[0]['previous_hash'] != '0' * 64:
            logger.warning("Genesis block hash mismatch")
            return False
        
        # Check chain integrity
        for i in range(1, len(ledger_entries)):
            current_previous = ledger_entries[i]['previous_hash']
            previous_hash = ledger_entries[i-1]['hash']
            
            if current_previous != previous_hash:
                logger.warning(f"Blockchain integrity broken at index {i}")
                return False
        
        logger.info("Blockchain integrity verified successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error verifying blockchain: {str(e)}")
        return False
