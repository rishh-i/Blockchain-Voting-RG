from database import db
from models.base import Base, get_current_utc
from datetime import datetime, timezone, timedelta

class OTPVerification(Base):
    """
    stores one time passwords for 2FA
    verification through email when logging in
    otp expires after 5 minutes
    """

    __tablename__ = "otp_verifications"

    email = db.Column(db.String(100), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<<OTP verification {self.email}; Verified: {self.is_verified}>>"

    def is_expired(self):
        # checks if the OTP has expired
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    @staticmethod
    def cleanup_old_otps():
        """
        deletes expired and already verified OTPs from the database
        """
        try:
            now = datetime.now(timezone.utc)
            # deletes OTPs
            OTPVerification.query.filter(
                db.or_(
                    OTPVerification.expires_at < now,
                    OTPVerification.is_verified == True
                )
            ).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error in deleting OTPs: {str(e)}")