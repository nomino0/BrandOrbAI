#!/usr/bin/env python3
"""
Simple script to test LinkedIn access token
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_linkedin_token():
    """Test if LinkedIn access token is valid"""
    
    # Get credentials from environment
    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    client_id = os.getenv('LINKEDIN_CLIENT_ID')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
    
    print("=== LinkedIn Token Test ===")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {'***' + client_secret[-4:] if client_secret else 'Not found'}")
    print(f"Access Token Length: {len(access_token) if access_token else 0}")
    print(f"Access Token Preview: {access_token[:30] + '...' if access_token else 'Not found'}")
    print()
    
    if not access_token:
        print("❌ No access token found in .env file")
        return False
    
    # Test the token by calling LinkedIn's userinfo endpoint
    url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        print("🔍 Testing LinkedIn access token...")
        response = requests.get(url, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Token is VALID!")
            print(f"User ID: {user_data.get('sub', 'Not found')}")
            print(f"Name: {user_data.get('name', 'Not found')}")
            print(f"Email: {user_data.get('email', 'Not found')}")
            return True
            
        elif response.status_code == 401:
            print("❌ Token is EXPIRED or INVALID")
            print(f"Error Response: {response.text}")
            return False
            
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {str(e)}")
        return False

if __name__ == "__main__":
    test_linkedin_token()
