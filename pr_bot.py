#!/usr/bin/env python3
"""
GitHub PR Bot - A simple bot that automatically adds a comment to pull requests when they are opened.

This bot listens for webhook events from GitHub, specifically for pull request events
with the "opened" action, and adds a comment to the PR.
"""

import os
import hmac
import hashlib
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GITHUB_PAT = os.getenv("GITHUB_PAT")
if not GITHUB_PAT:
    raise ValueError("GITHUB_PAT environment variable not set. Check your .env file.")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable not set. Check your .env file.")

# Initialize Flask app
app = Flask(__name__)

def verify_signature(payload_body, signature_header):
    """Verify that the webhook payload was sent from GitHub by validating the signature."""
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)

def post_pr_comment(repo_full_name, pr_number, comment_body):
    """Post a comment on a GitHub pull request."""
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": comment_body}
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"Successfully posted comment on PR #{pr_number} in {repo_full_name}")
        return True
    else:
        print(f"Failed to post comment: {response.status_code} {response.text}")
        return False

@app.route('/', methods=['GET'])
def index():
    """Root endpoint to check if the server is running."""
    return "Local GitHub PR Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint that receives GitHub events."""
    # Get the signature from the request headers
    signature_header = request.headers.get('X-Hub-Signature-256')
    
    # Get the event type from the request headers
    event_type = request.headers.get('X-GitHub-Event')
    
    # Get the payload body
    payload_body = request.data
    
    print("\n--- Webhook Received ---")
    
    # Verify the signature
    if not verify_signature(payload_body, signature_header):
        print("Signature verification failed!")
        return jsonify({"status": "error", "message": "Invalid signature"}), 401
    
    print("Signature verified successfully.")
    print(f"Event type: {event_type}")
    
    # Handle ping event (sent when webhook is first configured)
    if event_type == 'ping':
        print("Received ping event.")
        return jsonify({"status": "ping received successfully"})
    
    # Parse the payload
    try:
        payload = json.loads(payload_body)
        print("Payload parsed successfully.")
    except json.JSONDecodeError:
        print("Failed to parse payload.")
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400
    
    # Handle pull request event
    if event_type == 'pull_request':
        # Check if the action is 'opened' (new PR)
        action = payload.get('action')
        print(f"Action: {action}")
        
        if action == 'opened':
            # Get repository, PR number, and PR creator information
            repo_full_name = payload.get('repository', {}).get('full_name')
            pr_number = payload.get('number')
            pr_creator = payload.get('pull_request', {}).get('user', {}).get('login')
            pr_title = payload.get('pull_request', {}).get('title')
            
            print(f"Received new PR #{pr_number} in {repo_full_name} by {pr_creator}")
            print(f"PR Title: '{pr_title}'")
            
            # Create a comment for the PR
            comment = "PR Comment by Bot"
            
            try:
                # Post the comment on the PR
                success = post_pr_comment(repo_full_name, pr_number, comment)
                if success:
                    return jsonify({"status": "success", "message": "Comment posted on PR"})
                else:
                    return jsonify({"status": "error", "message": "Failed to post comment"}), 500
            except Exception as e:
                error_message = f"Failed to interact with GitHub API: {str(e)}"
                print(error_message)
                return jsonify({"status": "error", "message": error_message}), 500
        else:
            print(f"PR action '{action}' does not require a response.")
            return jsonify({"status": "ignored", "reason": f"PR action '{action}' does not require a response"})
    
    # For any other event or action, just acknowledge receipt
    return jsonify({"status": "acknowledged", "event": event_type})

if __name__ == '__main__':
    # Verify GitHub authentication
    auth_headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        auth_response = requests.get("https://api.github.com/user", headers=auth_headers)
        if auth_response.status_code == 200:
            username = auth_response.json().get('login')
            print(f"Successfully authenticated with GitHub as: {username}")
        else:
            print(f"Failed to authenticate with GitHub: {auth_response.status_code} {auth_response.text}")
    except Exception as e:
        print(f"Error authenticating with GitHub: {str(e)}")
    
    # Start the Flask server on a different port than the Issue Bot
    print("Starting PR Bot Flask server on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
