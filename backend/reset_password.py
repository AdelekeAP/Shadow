"""
Quick script to reset user password
"""
import sys
sys.path.append('/Users/useruser/Documents/shadow-final-year/backend')

from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

def reset_password(email: str, new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User with email {email} not found")
            return False

        # Hash new password
        user.password_hash = get_password_hash(new_password)
        db.commit()

        print(f"✅ Password reset successfully for {email}")
        print(f"   New password: {new_password}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Reset password for the main user
    email = "nicomannion6@gmail.com"
    new_password = "password123"  # Simple password for testing

    print(f"🔐 Resetting password for {email}...")
    reset_password(email, new_password)
