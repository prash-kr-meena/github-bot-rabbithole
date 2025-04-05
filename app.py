import os
import hmac
import hashlib
import json
from flask import Flask, request, jsonify, abort
from github import Github
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Get credentials and secret from environment variables
GITHUB_PAT = os.getenv("GITHUB_PAT")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Basic input validation
if not GITHUB_PAT:
    raise ValueError("GITHUB_PAT environment variable not set. Check your .env file.")
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable not set. Check your .env file.")

# Initialize PyGithub instance
try:
    g = Github(GITHUB_PAT)
    # Test authentication by getting the authenticated user (optional)
    auth_user = g.get_user()
    print(f"Successfully authenticated with GitHub as: {auth_user.login}")
except Exception as e:
    raise RuntimeError(f"Failed to authenticate with GitHub using the provided PAT: {e}")


def verify_signature(payload_body, signature_header):
    """Verify that the payload was sent from GitHub by validating the signature."""
    if not signature_header:
        print("ERROR: X-Hub-Signature-256 header is missing!")
        return False
    # Ensure payload_body is bytes
    if isinstance(payload_body, str):
        payload_body = payload_body.encode('utf-8')

    hash_object = hmac.new(WEBHOOK_SECRET.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        print(f"ERROR: Request signatures didn't match! Expected: {expected_signature}, Got: {signature_header}")
        return False
    print("Signature verified successfully.")
    return True

@app.route("/webhook", methods=['POST'])
def handle_webhook():
    """Handles incoming GitHub webhook events."""
    print("\n--- Webhook Received ---")

    # 1. Verify the signature
    signature = request.headers.get('X-Hub-Signature-256')
    # Use request.data which is the raw bytes payload
    if not verify_signature(request.data, signature):
        abort(400, 'Invalid signature')

    # 2. Check the event type
    event = request.headers.get('X-GitHub-Event')
    print(f"Event type: {event}")
    if event == "ping":
        print("Received ping event.")
        return jsonify({'status': 'ping received successfully'}), 200
    if event != "issue_comment":
        print(f"Ignoring event: {event}")
        return jsonify({'status': 'ignored', 'event': event}), 200

    # 3. Parse the JSON payload
    try:
        payload = request.get_json()
        if payload is None:
             raise json.JSONDecodeError("Payload is empty or not valid JSON", "", 0)
        print("Payload parsed successfully.")
        # print(json.dumps(payload, indent=2)) # Uncomment for detailed payload view
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        abort(400, 'Invalid JSON payload')

    # 4. Extract relevant information
    try:
        action = payload.get('action')
        print(f"Action: {action}")
        if action != 'created': # Only react to new comments
             print(f"Ignoring comment action: {action}")
             return jsonify({'status': 'ignored', 'action': action}), 200

        comment_body = payload['comment']['body']
        issue_number = payload['issue']['number']
        repo_full_name = payload['repository']['full_name']
        commenter_login = payload['comment']['user']['login']

        print(f"Received comment on {repo_full_name}# {issue_number} by {commenter_login}")
        print(f"Comment body: '{comment_body}'")

    except KeyError as e:
        print(f"Error parsing payload: Missing key {e}")
        abort(400, f'Malformed payload: Missing key {e}')
    except Exception as e:
        print(f"An unexpected error occurred during payload processing: {e}")
        abort(500, 'Internal server error during payload processing')


    # 5. Implement Bot Logic
    if comment_body.strip().lower() == "/greet":
        try:
            print(f"Detected '/greet' command in comment on issue #{issue_number}.")
            repo = g.get_repo(repo_full_name)
            issue = repo.get_issue(issue_number)

            # Create the reply comment
            reply_message = f"Hello @{commenter_login}! Thanks for the greeting! (Sent from my local bot)"
            issue.create_comment(reply_message)
            print(f"Posted reply to issue #{issue_number}: '{reply_message}'")
            return jsonify({'status': 'success', 'message': 'Replied to /greet command'}), 200

        except Exception as e:
            print(f"Error interacting with GitHub API: {e}")
            # Avoid aborting if the API call fails, just log it and return an error status
            return jsonify({'status': 'error', 'message': f'Failed to interact with GitHub API: {e}'}), 500

    else:
        print("Comment did not contain '/greet'. No action taken.")
        return jsonify({'status': 'ignored', 'reason': 'Command not found'}), 200

# Simple root endpoint for basic check
@app.route("/")
def index():
    return "Local GitHub Bot is running!", 200

if __name__ == "__main__":
    # Run on port 5000 for local development
    print("Starting Flask server on http://localhost:5000")
    # Use debug=True for development ONLY - provides auto-reload and detailed errors
    app.run(host='0.0.0.0', port=5000, debug=True)
