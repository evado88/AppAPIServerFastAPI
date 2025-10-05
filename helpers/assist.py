
import hashlib
from passlib.context import CryptContext
import datetime as dt

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


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
    print('starting', dt.datetime.now())
    hashed = pwd_context.hash(password)
    print('finishing', dt.datetime.now())
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