#!/usr/bin/env python3
"""
Test script for the GitHub PR Bot with AI Code Review.
This script simulates webhook events to test the PR bot functionality locally.
"""

import os
import json
import hmac
import hashlib
import requests
import unittest.mock
from dotenv import load_dotenv
import time
import tempfile
import shutil
import subprocess

# Load environment variables
load_dotenv()

# Configuration
BOT_URL = "http://localhost:5001/webhook"  # PR bot runs on port 5001
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
REPO_FULL_NAME = os.getenv("GITHUB_REPO", "your-username/your-repo")
PR_NUMBER = os.getenv("GITHUB_PR_NUMBER", "1")
PR_CREATOR = os.getenv("GITHUB_USERNAME", "your-username")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

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

def get_mock_pr_files():
    """Get mock PR files for testing."""
    # This function would normally make an API call to GitHub
    # For testing, we'll return a mock response
    return [
        {
            "sha": "abc123def456",
            "filename": "test_file.py",
            "status": "added",
            "additions": 10,
            "deletions": 0,
            "changes": 10,
            "blob_url": f"https://github.com/{REPO_FULL_NAME}/blob/abc123def456/test_file.py",
            "raw_url": f"https://github.com/{REPO_FULL_NAME}/raw/abc123def456/test_file.py",
            "contents_url": f"https://api.github.com/repos/{REPO_FULL_NAME}/contents/test_file.py?ref=abc123def456"
        }
    ]

def get_mock_file_content():
    """Get mock file content for testing."""
    # This function would normally make an API call to GitHub
    # For testing, we'll return mock content
    return """#!/usr/bin/env python3
# This is a test file for the PR bot

def hello_world():
    # A simple function that prints hello world
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
"""

def simulate_pr_opened_event():
    """Simulate a PR opened event."""
    print("Sending simulated webhook event for PR opened")
    
    # Generate a mock commit SHA
    commit_sha = "abc123def456789ghijklmnopqrstuvwxyz0123"
    
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
            "updated_at": "2025-04-05T12:00:00Z",
            "head": {
                "sha": commit_sha,
                "ref": "feature-branch",
                "repo": {
                    "id": 123456,
                    "full_name": REPO_FULL_NAME
                }
            },
            "base": {
                "sha": "base-sha-123456",
                "ref": "main",
                "repo": {
                    "id": 123456,
                    "full_name": REPO_FULL_NAME
                }
            }
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

def setup_mocks():
    """Set up mock responses for the PR bot's API calls."""
    import requests_mock
    
    # Create a session with mocked responses
    session = requests.Session()
    adapter = requests_mock.Adapter()
    session.mount('https://', adapter)
    
    # Mock the PR files endpoint
    pr_files_url = f"https://api.github.com/repos/{REPO_FULL_NAME}/pulls/{PR_NUMBER}/files"
    adapter.register_uri('GET', pr_files_url, json=get_mock_pr_files())
    
    # Mock the file content endpoint (this is a bit tricky because the URL contains a variable)
    # We'll use a custom matcher function
    def content_matcher(request):
        if "contents" in request.url and REPO_FULL_NAME in request.url:
            return True
        return False
    
    adapter.register_uri(
        'GET', 
        requests_mock.ANY, 
        additional_matcher=content_matcher,
        json={
            "encoding": "base64",
            "content": "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIFRoaXMgaXMgYSB0ZXN0IGZpbGUgZm9yIHRoZSBQUiBib3QKCmRlZiBoZWxsb193b3JsZCgpOgogICAgIyBBIHNpbXBsZSBmdW5jdGlvbiB0aGF0IHByaW50cyBoZWxsbyB3b3JsZAogICAgcHJpbnQoIkhlbGxvLCBXb3JsZCEiKQoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIGhlbGxvX3dvcmxkKCkK"  # base64 encoded content
        }
    )
    
    # Mock the Anthropic API response
    anthropic_url = "https://api.rabbithole.cred.club/messages"
    adapter.register_uri(
        'POST', 
        anthropic_url,
        json={
            "id": "msg_01234567890123456789",
            "type": "message",
            "role": "assistant",
            "model": "claude-3-7-sonnet-20250219",
            "content": [
                {
                    "type": "text",
                    "text": """
# Code Review

## Summary
The code is a simple Python script that defines a `hello_world()` function which prints "Hello, World!". Overall, the code is clean and follows good practices for a simple script.

## Specific Issues
No significant issues found.

## Suggestions
1. Consider adding a docstring to the `hello_world()` function to explain its purpose.
2. For better compatibility, you might want to use `if __name__ == "__main__":` guard (which you already have).

## Positive Aspects
- Clean and readable code
- Proper use of the `if __name__ == "__main__":` guard
- Good naming conventions
- Appropriate comments
"""
                }
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 150
            }
        }
    )
    
    return session

def create_test_repo():
    """Create a test repository for testing the PR review functionality."""
    repo_dir = os.path.join(tempfile.gettempdir(), "test_repo")
    
    # Clean up any existing test repository
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
    
    # Create a new directory
    os.makedirs(repo_dir)
    
    # Initialize a git repository
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    
    # Create a test file
    test_file_path = os.path.join(repo_dir, "test_file.py")
    with open(test_file_path, "w") as f:
        f.write(get_mock_file_content())
    
    # Add and commit the file
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    
    return repo_dir

def test_repository_cloning():
    """Test the repository cloning functionality."""
    print("\n3. Testing repository cloning...")
    
    # Import the PR review module
    import pr_review
    
    # Create a test repository
    repo_dir = create_test_repo()
    
    # Mock the clone_repository function to return the test repository
    with unittest.mock.patch('pr_review.clone_repository', return_value=repo_dir):
        # Test the get_file_content_from_repo function
        file_content = pr_review.get_file_content_from_repo(repo_dir, "test_file.py")
        
        if file_content and "hello_world" in file_content:
            print("Repository cloning test passed!")
        else:
            print("Repository cloning test failed!")
    
    return repo_dir

def test_ai_code_review():
    """Test the AI code review functionality."""
    print("\n4. Testing AI code review...")
    
    # Import the PR review module
    import pr_review
    
    # Create a test repository
    repo_dir = create_test_repo()
    
    # Create test file info
    file_info = {
        'path': 'test_file.py',
        'full_content': get_mock_file_content(),
        'diff': '@@ -0,0 +1,9 @@\n+#!/usr/bin/env python3\n+# This is a test file for the PR bot\n+\n+def hello_world():\n+    # A simple function that prints hello world\n+    print("Hello, World!")\n+\n+if __name__ == "__main__":\n+    hello_world()',
        'changed_sections': [{'start_line': 1, 'end_line': 9, 'content': ['#!/usr/bin/env python3', '# This is a test file for the PR bot', '', 'def hello_world():', '    # A simple function that prints hello world', '    print("Hello, World!")', '', 'if __name__ == "__main__":', '    hello_world()']}]
    }
    
    # Create test PR info
    pr_info = {
        'title': 'Test PR',
        'description': 'This is a test PR',
        'author': 'test-user',
        'number': 1
    }
    
    # Mock the Anthropic client
    with unittest.mock.patch('anthropic.Anthropic'):
        # Mock the get_ai_code_review function to return a test review
        with unittest.mock.patch('pr_review.get_ai_code_review', return_value="Test code review"):
            # Test the review_pr_files function
            with unittest.mock.patch('pr_review.clone_repository', return_value=repo_dir):
                # Test the analyze_pr_file function
                with unittest.mock.patch('pr_review.analyze_pr_file', return_value=file_info):
                    reviews = pr_review.review_pr_files(
                        REPO_FULL_NAME,
                        PR_NUMBER,
                        get_mock_pr_files(),
                        "main",
                        "feature-branch",
                        pr_info
                    )
                    
                    if reviews and len(reviews) > 0 and reviews[0]['review'] == "Test code review":
                        print("AI code review test passed!")
                    else:
                        print("AI code review test failed!")

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
    
    print("\nNote: This test script simulates a PR opened event.")
    print("The PR bot will attempt to fetch PR files and content from GitHub.")
    print("If you're using placeholder values for GITHUB_REPO, the bot will fall back to posting a general comment.")
    print("For full testing with review comments, set up real GitHub repository values in your .env file.")
    
    # Ask the user which tests to run
    print("\nAvailable tests:")
    print("1. Ping event test")
    print("2. PR opened event test")
    print("3. Repository cloning test")
    print("4. AI code review test")
    print("5. Run all tests")
    
    choice = input("\nEnter the number of the test to run (or 5 for all): ")
    
    if choice == "1" or choice == "5":
        print("\n1. Testing ping event...")
        test_ping_event()
    
    if choice == "2" or choice == "5":
        print("\n2. Testing PR opened event...")
        simulate_pr_opened_event()
    
    if choice == "3" or choice == "5":
        print("\n3. Testing repository cloning...")
        test_repository_cloning()
    
    if choice == "4" or choice == "5":
        print("\n4. Testing AI code review...")
        test_ai_code_review()
    
    print("\nTests completed. Check the bot's console output for more details.")
