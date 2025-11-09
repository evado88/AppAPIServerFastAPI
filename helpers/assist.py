
import hashlib
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import calendar

USER_MEMBER = 1
USER_ADMIN = 2

UPLOAD_DIR = "uploads"

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
CURRENT_TIME_ZONE = "Africa/Lusaka"

STATUS_SUBMITTED = 2
STATUS_APPROVED = 4
STATUS_REJECTED = 5

TRANSACTION_SAVINGS = 1
TRANSACTION_SHARE = 2
TRANSACTION_LOAN = 3
TRANSACTION_LOAN_PAYMENT = 4
TRANSACTION_INTEREST_CHARGED = 5
TRANSACTION_INTEREST_PAID = 6
TRANSACTION_SOCIAL_FUND = 7
TRANSACTION_PENALTY_CHARGED = 8
TRANSACTION_PENALTY_PAID= 9

STATE_OPEN = 1
STATE_CLOSED = 2

REVIEW_ACTION_REJECT = 1
REVIEW_ACTION_APPROVE = 2

APPROVAL_STAGE_SUBMITTED = 2
APPROVAL_STAGE_PRIMARY = 3
APPROVAL_STAGE_SECONDARY = 4
APPROVAL_STAGE_GUARANTOR = 5
APPROVAL_STAGE_POP_UPLOAD = 6
APPROVAL_STAGE_POP_APPROVAL = 7
APPROVAL_STAGE_APPROVED = 8

RESPONSE_NO = 1
RESPONSE_YES = 2

PENALTY_LATE_POSTING = 1
PENALTY_MISSED_MEETING = 2
PENALTY_LATE_MEETING = 3


NOTIFY_WAITING= 1
NOTIFY_SENT = 2

def get_safe_name(input: str):
    return input.replace(" ", "")

def get_current_date(date = True):
    # Set your timezon
    tz = ZoneInfo(CURRENT_TIME_ZONE)

    # Get current date with timezone
    now = datetime.now(tz)
    
    if date:
        now = datetime(now.year, now.month, now.day)
    
    return now

def get_first_month_day(inputDate = None):
    # Set your timezon
    tz = ZoneInfo(CURRENT_TIME_ZONE)

    # Get current date with timezone
    now = datetime.now(tz) if inputDate == None else inputDate

    # Get first day of current month
    first_day = datetime(now.year, now.month, 1, tzinfo=tz)

    return first_day

def get_last_month_day(inputDate = None):
    # Set your timezon
    tz = ZoneInfo(CURRENT_TIME_ZONE)

    # Get current date with timezone
    now = datetime.now(tz) if inputDate == None else inputDate

    # Get last day of current month
    last_day_num = calendar.monthrange(now.year, now.month)[1]
    last_day = datetime(now.year, now.month, last_day_num, tzinfo=tz)

    return last_day
    
def encode_sha256(input):
    '''
    Encodes the specified input to SHA-256
    
    Args:
        input (string): The input to encode.


    Returns:
        string: The encode string in SHA-256 format.
    '''
    # Create a SHA-256 hash object
    hasher = hashlib.sha256()
    # Update the hash object with the byte-encoded message
    hasher.update(input.encode("utf-8"))
    # Get the hexadecimal representation of the hash
    sha256_result = hasher.hexdigest()
    return sha256_result


# Create a password context using bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    '''
    Hash a plain password using bcrypt
    
    Args:
        passwrd (string): The password to hash.

    Returns:
        string: The hashed password string.
    '''
    hashed = pwd_context.hash(password)
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''
    Verify a plain password against a hash
    
    Args:
        plain_password (string): The plain password to verify.
        hashed_password (string): The password hash to verify against.
    Returns:
        bool: Returns true if the password matches the hash, false otherwise
    '''
    return pwd_context.verify(plain_password, hashed_password)