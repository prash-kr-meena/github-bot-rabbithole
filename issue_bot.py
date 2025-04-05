#!/usr/bin/env python3
"""
GitHub Issue Bot - A simple bot that responds to issue comments with a greeting.

This bot listens for webhook events from GitHub, specifically for issue comments
containing the "/greet" command, and responds with a personalized greeting.
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

def post_comment(repo_full_name, issue_number, comment_body):
    """Post a comment on a GitHub issue."""
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": comment_body}
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"Successfully posted comment on {repo_full_name}#{issue_number}")
        return True
    else:
        print(f"Failed to post comment: {response.status_code} {response.text}")
        return False

@app.route('/', methods=['GET'])
def index():
    """Root endpoint to check if the server is running."""
    return "Local GitHub Bot is running!"

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
    
    # Handle issue comment event
    if event_type == 'issue_comment':
        # Check if the action is 'created' (new comment)
        action = payload.get('action')
        print(f"Action: {action}")
        
        if action == 'created':
            # Get repository, issue number, and comment information
            repo_full_name = payload.get('repository', {}).get('full_name')
            issue_number = payload.get('issue', {}).get('number')
            comment_body = payload.get('comment', {}).get('body', '')
            commenter_login = payload.get('comment', {}).get('user', {}).get('login')
            
            print(f"Received comment on {repo_full_name}# {issue_number} by {commenter_login}")
            print(f"Comment body: '{comment_body}'")
            
            # Check if the comment contains the "/greet" command
            if comment_body.strip() == '/greet':
                print(f"Detected '/greet' command in comment on issue #{issue_number}.")
                
                # Create a personalized greeting
                greeting = f"👋 Hello @{commenter_login}! Thanks for using the greeting command."
                
                try:
                    # Post the greeting as a comment
                    success = post_comment(repo_full_name, issue_number, greeting)
                    if success:
                        return jsonify({"status": "success", "message": "Greeting posted"})
                    else:
                        return jsonify({"status": "error", "message": "Failed to post greeting"}), 500
                except Exception as e:
                    error_message = f"Error interacting with GitHub API: {str(e)}"
                    print(error_message)
                    return jsonify({"status": "error", "message": error_message}), 500
            else:
                print(f"Comment did not contain '/greet'. No action taken.")
                return jsonify({"status": "ignored", "reason": "Command not found"})
    
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
    
    # Start the Flask server
    print("Starting Issue Bot Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
