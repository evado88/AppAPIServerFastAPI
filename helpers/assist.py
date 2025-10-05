
import hashlib

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