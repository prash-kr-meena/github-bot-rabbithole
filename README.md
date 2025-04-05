# Simple GitHub Bot - Local Development

A simple GitHub bot that responds to issue comments with a greeting when triggered with the `/greet` command. This project is designed for local development and testing.

## Features

- Listens for issue comments in a GitHub repository
- Responds to `/greet` commands with a personalized greeting
- Runs locally with webhook events forwarded via ngrok

## Prerequisites

- Python 3.6+
- pip (Python package installer)
- GitHub account
- A GitHub repository you own (for testing)
- ngrok installed ([See detailed installation guide](NGROK_SETUP.md))

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd simple-github-bot-local
```

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (cmd)
venv\Scripts\activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create GitHub Personal Access Token (PAT)

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token" (or "Generate new token (classic)")
3. Name: `local-dev-issue-bot-token`
4. Expiration: Choose a suitable duration
5. Scopes: Select `repo` (or more granular permissions like `issues:write`)
6. Click "Generate token"
7. **Important**: Copy the generated token immediately

### 5. Configure Environment Variables

1. Edit the `.env` file in the project root
2. Replace `YOUR_COPIED_PERSONAL_ACCESS_TOKEN` with your actual PAT
3. Use the included utility script to generate a webhook secret:
   ```bash
   python generate_secret.py
   ```
   This will generate a secure random string and offer to update your `.env` file automatically.
   
   Alternatively, you can generate a secret manually with `openssl rand -hex 32` and update the `.env` file yourself.

### 6. Test Your Setup

You can test individual components of your setup:

```bash
# Test GitHub authentication
python test_github_auth.py

# Test ngrok connectivity
python test_ngrok.py

# Test webhook simulation
python test_bot.py
```

Or run a comprehensive test suite that checks everything:

```bash
python run_tests.py
```

The comprehensive test suite will:
1. Verify your GitHub authentication
2. Check ngrok connectivity
3. Test if the Flask application can start
4. Simulate webhook events to test the bot's functionality

This is the recommended way to verify your entire setup before configuring GitHub webhooks.

> **Note:** The test suite runs each test in sequence and will stop if any test fails. Make sure you've configured your `.env` file with the appropriate values before running the tests.

## Running the Bot Locally

### Phase 3: Testing the Bot Locally

#### Step 1: Start the Flask Application

```bash
python app.py
```

You should see output indicating the server is running on http://localhost:5000.

#### Step 2: Expose Local Server with ngrok

In a new terminal window:

```bash
# Start ngrok on the same port as your Flask app (5000)
ngrok http 5000
```

ngrok will display a forwarding URL (e.g., `https://a1b2c3d4.ngrok.io`). Copy this URL as you'll need it for the next step.

Alternatively, you can use the included utility script to check ngrok status and get the URL:

```bash
python test_ngrok.py
```

This script will:
- Check if ngrok is running
- Display the public URL for your webhook
- Test if the webhook endpoint is accessible
- Offer to start ngrok if it's not already running

> **Note:** For detailed instructions on installing and running ngrok, including troubleshooting tips, see the [ngrok setup guide](NGROK_SETUP.md).

#### Step 3: Configure GitHub Webhook

1. Go to your GitHub repository
2. Click on "Settings" → "Webhooks" → "Add webhook"
3. Configure the webhook:
   - Payload URL: `https://your-ngrok-url/webhook` (replace with your actual ngrok URL)
   - Content type: `application/json`
   - Secret: Enter the same webhook secret you used in your `.env` file
   - Events: Select "Issue comments" only
   - Active: Check this box
4. Click "Add webhook"

GitHub will send a ping event to verify the webhook is working. Check your Flask application logs to confirm it received the ping.

#### Step 4: Test the Bot

1. Create a new issue in your repository
2. Add a comment with just `/greet` in the body
3. Watch your Flask application logs to see the webhook being received
4. The bot should automatically reply to your comment with a greeting

#### Step 5: Debugging

If the bot doesn't respond:

1. Check the Flask application logs for errors
2. Verify the webhook was received (you should see "Webhook Received" in the logs)
3. Ensure your PAT has the correct permissions
4. Check that the webhook secret matches between GitHub and your `.env` file
5. Verify ngrok is running and the URL is correctly configured in GitHub

## Extending the Bot

You can extend this bot by:

1. Adding more commands (modify the bot logic in `app.py`)
2. Responding to different GitHub events (modify the webhook handler)
3. Adding more complex interactions with the GitHub API

## Shutting Down

1. Stop the Flask application (Ctrl+C)
2. Stop ngrok (Ctrl+C)
3. Deactivate the virtual environment:
   ```bash
   deactivate
   ```

## Security Notes

- Never commit your `.env` file or expose your PAT or webhook secret
- For production use, consider more secure deployment options
- The webhook secret is crucial for verifying that requests come from GitHub
