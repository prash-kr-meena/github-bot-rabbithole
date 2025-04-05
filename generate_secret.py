#!/usr/bin/env python3
"""
Utility script to generate a secure webhook secret and update the .env file.
"""

import os
import secrets
import string
import re
from dotenv import load_dotenv

def generate_secure_secret(length=32):
    """Generate a cryptographically secure random string."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def update_env_file(secret):
    """Update the .env file with the new webhook secret."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    # Check if .env file exists
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        return False
    
    # Read the current content
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Replace the webhook secret placeholder or existing value
    pattern = r'WEBHOOK_SECRET=.*'
    replacement = f'WEBHOOK_SECRET={secret}'
    
    if re.search(pattern, content):
        # Replace existing webhook secret
        new_content = re.sub(pattern, replacement, content)
    else:
        # Add webhook secret if not present
        new_content = content + f'\n{replacement}\n'
    
    # Write the updated content back to the file
    with open(env_path, 'w') as f:
        f.write(new_content)
    
    return True

if __name__ == "__main__":
    print("GitHub Bot - Webhook Secret Generator")
    print("=====================================")
    
    # Generate a secure secret
    secret = generate_secure_secret(64)  # 64 characters for extra security
    
    print(f"Generated webhook secret: {secret}")
    
    # Ask if user wants to update .env file
    update = input("\nDo you want to update the .env file with this secret? (y/n): ").strip().lower()
    
    if update == 'y':
        if update_env_file(secret):
            print("\nSuccess! The .env file has been updated with the new webhook secret.")
            print("Make sure to use this same secret when configuring your GitHub webhook.")
        else:
            print("\nFailed to update the .env file.")
            print(f"Please manually set WEBHOOK_SECRET={secret} in your .env file.")
    else:
        print("\nThe .env file was not updated.")
        print("If you want to use this secret, manually set it in your .env file:")
        print(f"WEBHOOK_SECRET={secret}")
    
    print("\nRemember to keep this secret secure and never commit it to version control!")
