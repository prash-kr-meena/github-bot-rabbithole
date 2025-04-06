#!/usr/bin/env python3
"""
GitHub PR Bot - A bot that automatically reviews pull requests when they are opened.

This bot listens for webhook events from GitHub, specifically for pull request events
with the "opened" action, and adds AI-generated code review comments to the PR.
"""

import os
import hmac
import hashlib
import json
import requests
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import the PR review module
import pr_review

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

def get_pr_files(repo_full_name, pr_number):
    """Get the list of files in a pull request."""
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get PR files: {response.status_code} {response.text}")
        return None

def get_file_content(repo_full_name, file_path, commit_sha):
    """Get the content of a file at a specific commit."""
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}?ref={commit_sha}"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        content_data = response.json()
        if content_data.get("encoding") == "base64":
            import base64
            content = base64.b64decode(content_data.get("content")).decode("utf-8")
            return content
        return None
    else:
        print(f"Failed to get file content: {response.status_code} {response.text}")
        return None

def find_first_code_line(content):
    """Find the first non-empty line of code in a file."""
    if not content:
        return None
    
    lines = content.split("\n")
    for i, line in enumerate(lines):
        # Skip empty lines and comment-only lines
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith(("#", "//", "/*", "*", "'")):
            return {
                "line_number": i + 1,  # GitHub line numbers are 1-based
                "content": line
            }
    
    return None

def post_pr_review_comment(repo_full_name, pr_number, commit_id, path, position, body):
    """Post a review comment on a specific line of code in a pull request."""
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "commit_id": commit_id,
        "path": path,
        "position": position,  # Line number in the diff
        "body": body
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"Successfully posted review comment on PR #{pr_number} in {repo_full_name}")
        return True
    else:
        print(f"Failed to post review comment: {response.status_code} {response.text}")
        return False

def post_pr_comment(repo_full_name, pr_number, comment_body):
    """Post a general comment on a GitHub pull request."""
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
            pr_body = payload.get('pull_request', {}).get('body', '')
            head_sha = payload.get('pull_request', {}).get('head', {}).get('sha')
            base_branch = payload.get('pull_request', {}).get('base', {}).get('ref', 'main')
            head_branch = payload.get('pull_request', {}).get('head', {}).get('ref')
            
            print(f"Received new PR #{pr_number} in {repo_full_name} by {pr_creator}")
            print(f"PR Title: '{pr_title}'")
            print(f"Base branch: {base_branch}, Head branch: {head_branch}")
            
            try:
                # First, get the list of files in the PR
                pr_files = get_pr_files(repo_full_name, pr_number)
                
                if not pr_files or len(pr_files) == 0:
                    print("No files found in the PR. Posting a general comment instead.")
                    # Post a general comment if no files are found
                    success = post_pr_comment(repo_full_name, pr_number, "PR Comment by Bot - No files found to review")
                    if success:
                        return jsonify({"status": "success", "message": "General comment posted on PR"})
                    else:
                        return jsonify({"status": "error", "message": "Failed to post general comment"}), 500
                
                # Post an initial comment to let the user know the bot is reviewing the PR
                initial_comment = (
                    "# 🤖 AI Code Review in Progress\n\n"
                    "I'm analyzing your pull request and will provide a detailed code review shortly.\n\n"
                    f"Reviewing {len(pr_files)} file(s) changed in this PR.\n\n"
                    "Please wait while I process the code..."
                )
                post_pr_comment(repo_full_name, pr_number, initial_comment)
                
                # Prepare PR info for the review
                pr_info = {
                    'title': pr_title,
                    'description': pr_body,
                    'author': pr_creator,
                    'number': pr_number
                }
                
                # Generate AI reviews for each file in the PR
                print(f"Generating AI reviews for {len(pr_files)} files...")
                reviews = pr_review.review_pr_files(
                    repo_full_name, 
                    pr_number, 
                    pr_files, 
                    base_branch, 
                    head_branch, 
                    pr_info
                )
                
                # Post review comments for each file
                success_count = 0
                failure_count = 0
                
                for review_data in reviews:
                    file_info = review_data['file']
                    review_content = review_data['review']
                    file_path = file_info['path']
                    
                    print(f"Posting review for file: {file_path}")
                    
                    # Post the AI-generated review as a comment on the PR
                    comment = f"# AI Code Review for `{file_path}`\n\n{review_content}"
                    
                    # First, try to post the review on the first line of the first changed section
                    if file_info['changed_sections'] and len(file_info['changed_sections']) > 0:
                        first_section = file_info['changed_sections'][0]
                        line_number = first_section['start_line']
                        
                        success = post_pr_review_comment(
                            repo_full_name,
                            pr_number,
                            head_sha,
                            file_path,
                            line_number,
                            comment
                        )
                        
                        if success:
                            success_count += 1
                        else:
                            # If posting as a review comment fails, post as a general comment
                            general_success = post_pr_comment(repo_full_name, pr_number, comment)
                            if general_success:
                                success_count += 1
                            else:
                                failure_count += 1
                    else:
                        # If no changed sections were identified, post as a general comment
                        general_success = post_pr_comment(repo_full_name, pr_number, comment)
                        if general_success:
                            success_count += 1
                        else:
                            failure_count += 1
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(1)
                
                # Post a summary comment
                summary = (
                    "# 🤖 AI Code Review Complete\n\n"
                    f"I've reviewed {len(reviews)} file(s) in this pull request.\n\n"
                    f"- Successfully posted {success_count} review comment(s)\n"
                    f"- Failed to post {failure_count} review comment(s)\n\n"
                    "Please review the comments and make any necessary changes. "
                    "If you have any questions about the review, feel free to ask!"
                )
                post_pr_comment(repo_full_name, pr_number, summary)
                
                return jsonify({
                    "status": "success", 
                    "message": f"Posted {success_count} review comments on PR",
                    "failures": failure_count
                })
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
