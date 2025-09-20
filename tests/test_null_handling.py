# Test script to verify NULL handling fix
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../app'))

from database import DatabaseConnection

def test_safe_conversions():
    """Test the safe conversion methods"""
    db = DatabaseConnection()
    
    # Test safe_float_conversion
    print("Testing safe_float_conversion:")
    test_cases_float = [
        (None, 0.0),
        ('NULL', 0.0),
        ('null', 0.0),
        ('', 0.0),
        ('  NULL  ', 0.0),
        ('123.45', 123.45),
        (123.45, 123.45),
        ('not_a_number', 0.0),
        (0, 0.0),
        ('0', 0.0)
    ]
    
    for input_val, expected in test_cases_float:
        result = db._safe_float_conversion(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} Input: {repr(input_val)} -> Expected: {expected} -> Got: {result}")
    
    print("\nTesting safe_int_conversion:")
    test_cases_int = [
        (None, 0),
        ('NULL', 0),
        ('null', 0),
        ('', 0),
        ('  NULL  ', 0),
        ('123', 123),
        (123, 123),
        ('not_a_number', 0),
        (0, 0),
        ('0', 0),
        ('123.45', 123)  # Should truncate to int
    ]
    
    for input_val, expected in test_cases_int:
        result = db._safe_int_conversion(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} Input: {repr(input_val)} -> Expected: {expected} -> Got: {result}")

if __name__ == "__main__":
    print("Testing NULL handling fix...\n")
    test_safe_conversions()
    print("\n✅ All NULL handling tests completed!")