#!/usr/bin/env python3
"""
Test script to verify .env configuration is working correctly
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env():
    """Test environment variables"""
    print("🔍 Testing .env configuration...")
    
    required_vars = [
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_DATABASE',
        'POSTGRES_PASSWORD',
        'POSTGRES_USERNAME',
        'POSTGRES_USER'
    ]
    
    config = {}
    for var in required_vars:
        value = os.getenv(var)
        if value:
            config[var] = value
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    if all(os.getenv(var) for var in required_vars[:4]):  # Check required ones
        host = os.getenv('POSTGRES_HOST')
        port = os.getenv('POSTGRES_PORT')
        database = os.getenv('POSTGRES_DATABASE')
        user = os.getenv('POSTGRES_USERNAME', os.getenv('POSTGRES_USER', 'root'))
        password = os.getenv('POSTGRES_PASSWORD')
        
        conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        print(f"\n🔗 Connection string format: {conn_string}")
        return True
    else:
        print("\n❌ Missing required environment variables")
        return False

if __name__ == "__main__":
    test_env()