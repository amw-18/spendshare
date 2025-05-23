import pytest
from app.core.security import get_password_hash, verify_password

def test_password_hashing_and_verification():
    password = "mYsEcReTpAsSwOrD123!"
    
    hashed_password = get_password_hash(password)
    
    # Check that the hashed password is not the same as the original password
    assert hashed_password != password
    
    # Check that the hashed password is a string
    assert isinstance(hashed_password, str)
    
    # Verify the correct password
    assert verify_password(password, hashed_password) == True
    
    # Verify an incorrect password
    assert verify_password("wRoNgPaSsWoRd!321", hashed_password) == False

def test_verify_password_with_different_hashes_for_same_password():
    password = "another_secure_password"
    
    hashed_password1 = get_password_hash(password)
    hashed_password2 = get_password_hash(password)
    
    # bcrypt generates a different hash each time due to salting
    assert hashed_password1 != hashed_password2 
    
    # Both hashes should still verify correctly against the original password
    assert verify_password(password, hashed_password1) == True
    assert verify_password(password, hashed_password2) == True

def test_get_password_hash_empty_password():
    # Test how get_password_hash handles an empty string.
    # Passlib's bcrypt usually handles this by hashing it.
    password = ""
    hashed_password = get_password_hash(password)
    assert isinstance(hashed_password, str)
    assert verify_password(password, hashed_password) == True

# Note: Since these are not async functions, the tests don't need @pytest.mark.asyncio
# If JWT token functions were added to security.py and they were async,
# their tests would need the asyncio marker.
