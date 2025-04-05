#!/usr/bin/env python3
"""
Test script for the GitHub bot.
This script simulates a webhook event from GitHub to test the bot locally.
"""

import json
import hmac
import hashlib
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable not set. Check your .env file.")

BOT_URL = "http://localhost:5000/webhook"  # Local bot URL
REPO_FULL_NAME = "your-username/your-repo"  # Replace with your actual repo
ISSUE_NUMBER = 1  # Replace with an actual issue number in your repo
COMMENTER_LOGIN = "your-username"  # Replace with your GitHub username

def create_signature(payload_body):
    """Create a signature for the payload using the webhook secret."""
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body.encode('utf-8'),
        digestmod=hashlib.sha256
    )
    return "sha256=" + hash_object.hexdigest()

def simulate_issue_comment_event(comment_body):
    """Simulate a GitHub issue comment event."""
    # Create a payload similar to what GitHub would send
    payload = {
        "action": "created",
        "issue": {
            "number": ISSUE_NUMBER
        },
        "comment": {
            "body": comment_body,
            "user": {
                "login": COMMENTER_LOGIN
            }
        },
        "repository": {
            "full_name": REPO_FULL_NAME
        }
    }
    
    # Convert payload to JSON string
    payload_body = json.dumps(payload)
    
    # Create signature
    signature = create_signature(payload_body)
    
    # Set headers
    headers = {
        "X-Hub-Signature-256": signature,
        "X-GitHub-Event": "issue_comment",
        "Content-Type": "application/json"
    }
    
    # Send request to bot
    print(f"Sending simulated webhook event with comment: '{comment_body}'")
    response = requests.post(BOT_URL, data=payload_body, headers=headers)
    
    # Print response
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    return response

def test_ping_event():
    """Simulate a GitHub ping event."""
    payload = {"zen": "Keep it simple."}
    payload_body = json.dumps(payload)
    signature = create_signature(payload_body)
    
    headers = {
        "X-Hub-Signature-256": signature,
        "X-GitHub-Event": "ping",
        "Content-Type": "application/json"
    }
    
    print("Sending simulated ping event")
    response = requests.post(BOT_URL, data=payload_body, headers=headers)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    return response

if __name__ == "__main__":
    print("GitHub Bot Test Script")
    print("=====================")
    print(f"Bot URL: {BOT_URL}")
    print(f"Repository: {REPO_FULL_NAME}")
    print(f"Issue Number: {ISSUE_NUMBER}")
    print(f"Commenter: {COMMENTER_LOGIN}")
    print("=====================")
    
    # First, test if the server is running
    try:
        root_response = requests.get("http://localhost:5000/")
        print(f"Server status: {root_response.status_code} - {root_response.text.strip()}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the bot server. Make sure it's running on http://localhost:5000")
        exit(1)
    
    print("\n1. Testing ping event...")
    test_ping_event()
    
    print("\n2. Testing /greet command...")
    simulate_issue_comment_event("/greet")
    
    print("\n3. Testing non-command comment...")
    simulate_issue_comment_event("This is a regular comment, not a command.")
    
    print("\nTests completed. Check the bot's console output for more details.")
