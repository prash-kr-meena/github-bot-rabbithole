#!/usr/bin/env python3
"""
Test script for the GitHub PR Bot.
This script simulates webhook events to test the PR bot functionality locally.
"""

import os
import json
import hmac
import hashlib
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configuration
BOT_URL = "http://localhost:5001/webhook"  # PR bot runs on port 5001
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
REPO_FULL_NAME = os.getenv("GITHUB_REPO", "your-username/your-repo")
PR_NUMBER = os.getenv("GITHUB_PR_NUMBER", "1")
PR_CREATOR = os.getenv("GITHUB_USERNAME", "your-username")

def sign_payload(payload):
    """Create a GitHub-compatible HMAC signature for the webhook payload."""
    if not WEBHOOK_SECRET:
        print("WARNING: WEBHOOK_SECRET not set in .env file")
        return ""
    
    mac = hmac.new(WEBHOOK_SECRET.encode(), payload.encode(), hashlib.sha256)
    return f"sha256={mac.hexdigest()}"

def send_webhook_event(event_type, payload):
    """Send a simulated webhook event to the bot."""
    payload_json = json.dumps(payload)
    signature = sign_payload(payload_json)
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": event_type,
        "X-Hub-Signature-256": signature,
        "User-Agent": "GitHub-Hookshot/Test"
    }
    
    response = requests.post(BOT_URL, data=payload_json, headers=headers)
    
    print(f"Response status code: {response.status_code}")
    try:
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response body: {response.text}")
    
    return response

def test_ping_event():
    """Send a ping event to test the webhook endpoint."""
    print("Sending simulated ping event")
    
    payload = {
        "zen": "Keep it logically awesome.",
        "hook_id": 123456,
        "hook": {
            "type": "Repository",
            "id": 123456,
            "name": "web",
            "active": True,
            "events": ["pull_request"],
            "config": {
                "content_type": "json",
                "insecure_ssl": "0",
                "url": BOT_URL
            }
        },
        "repository": {
            "id": 123456,
            "full_name": REPO_FULL_NAME,
            "private": False
        },
        "sender": {
            "login": PR_CREATOR
        }
    }
    
    return send_webhook_event("ping", payload)

def simulate_pr_opened_event():
    """Simulate a PR opened event."""
    print("Sending simulated webhook event for PR opened")
    
    payload = {
        "action": "opened",
        "number": int(PR_NUMBER),
        "pull_request": {
            "url": f"https://api.github.com/repos/{REPO_FULL_NAME}/pulls/{PR_NUMBER}",
            "id": 123456789,
            "number": int(PR_NUMBER),
            "state": "open",
            "title": "Test PR for bot",
            "user": {
                "login": PR_CREATOR
            },
            "body": "This is a test PR to trigger the PR bot",
            "created_at": "2025-04-05T12:00:00Z",
            "updated_at": "2025-04-05T12:00:00Z"
        },
        "repository": {
            "id": 123456,
            "full_name": REPO_FULL_NAME,
            "private": False,
            "owner": {
                "login": PR_CREATOR
            }
        },
        "sender": {
            "login": PR_CREATOR
        }
    }
    
    return send_webhook_event("pull_request", payload)

if __name__ == "__main__":
    print("GitHub PR Bot Test Script")
    print("=====================")
    print(f"Bot URL: {BOT_URL}")
    print(f"Repository: {REPO_FULL_NAME}")
    print(f"PR Number: {PR_NUMBER}")
    print(f"PR Creator: {PR_CREATOR}")
    print("=====================")
    
    # First, test if the server is running
    try:
        root_response = requests.get("http://localhost:5001/")
        print(f"Server status: {root_response.status_code} - {root_response.text.strip()}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the PR bot server. Make sure it's running on http://localhost:5001")
        exit(1)
    
    print("\n1. Testing ping event...")
    test_ping_event()
    
    print("\n2. Testing PR opened event...")
    simulate_pr_opened_event()
    
    print("\nTests completed. Check the bot's console output for more details.")
