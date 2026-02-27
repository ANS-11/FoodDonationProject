import sqlite3
import bcrypt
import os


# =====================================================
# DATABASE PATH
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "food_donation.db")


# =====================================================
# CONNECT DATABASE (SAFE VERSION)
# =====================================================

def connect_db():
    """
    Creates a NEW database connection every time.
    This is the CORRECT approach for Streamlit + SQLite.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# HASH PASSWORD
# =====================================================

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )
    return hashed.decode("utf-8")


# =====================================================
# VERIFY PASSWORD
# =====================================================

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        print("PASSWORD VERIFY ERROR:", e)
        return False


# =====================================================
# DEBUG DB LOCATION
# =====================================================

def debug_db_location():
    print("USING DATABASE AT:")
    print(DB_PATH)