# GitHub Bots - Local Development

This project contains two GitHub bots designed for local development and testing:

1. **Issue Bot**: Responds to issue comments with a greeting when triggered with the `/greet` command
2. **PR Bot**: Automatically adds code review comments to pull requests when they are opened

## Features

### Issue Bot
- Listens for issue comments in a GitHub repository
- Responds to `/greet` commands with a personalized greeting
- Runs locally with webhook events forwarded via ngrok

### PR Bot
- Listens for pull request events in a GitHub repository
- Automatically adds a code review comment on the first line of code in the first file of a new PR
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

# Test Issue Bot webhook simulation
python test_bot.py

# Test PR Bot webhook simulation
python test_pr_bot.py
```

Or run a comprehensive test suite that checks everything:

```bash
python run_tests.py
```

The comprehensive test suite will:
1. Verify your GitHub authentication
2. Check ngrok connectivity
3. Test if the Issue Bot can start
4. Simulate webhook events to test the bots' functionality

This is the recommended way to verify your entire setup before configuring GitHub webhooks.

> **Note:** The test suite runs each test in sequence and will stop if any test fails. Make sure you've configured your `.env` file with the appropriate values before running the tests.

## Running the Bots Locally

### Running the Issue Bot

#### Step 1: Start the Issue Bot

```bash
python issue_bot.py
```

You should see output indicating the server is running on http://localhost:5000.

#### Step 2: Expose Local Server with ngrok

In a new terminal window:

```bash
# Start ngrok on the same port as your Issue Bot (5000)
ngrok http 5000
```

ngrok will display a forwarding URL (e.g., `https://a1b2c3d4.ngrok.io`). Copy this URL as you'll need it for the next step.

#### Step 3: Configure GitHub Webhook for Issue Bot

1. Go to your GitHub repository
2. Click on "Settings" → "Webhooks" → "Add webhook"
3. Configure the webhook:
   - Payload URL: `https://your-ngrok-url/webhook` (replace with your actual ngrok URL)
   - Content type: `application/json`
   - Secret: Enter the same webhook secret you used in your `.env` file
   - Events: Select "Issue comments" only
   - Active: Check this box
4. Click "Add webhook"

#### Step 4: Test the Issue Bot

1. Create a new issue in your repository
2. Add a comment with just `/greet` in the body
3. Watch your Issue Bot logs to see the webhook being received
4. The bot should automatically reply to your comment with a greeting

### Running the PR Bot

#### Step 1: Start the PR Bot

```bash
python pr_bot.py
```

You should see output indicating the server is running on http://localhost:5001.

#### Step 2: Expose Local Server with ngrok

In a new terminal window:

```bash
# Start ngrok on the same port as your PR Bot (5001)
ngrok http 5001
```

ngrok will display a forwarding URL (e.g., `https://b2c3d4e5.ngrok.io`). Copy this URL as you'll need it for the next step.

#### Step 3: Configure GitHub Webhook for PR Bot

1. Go to your GitHub repository
2. Click on "Settings" → "Webhooks" → "Add webhook"
3. Configure the webhook:
   - Payload URL: `https://your-ngrok-url/webhook` (replace with your actual ngrok URL)
   - Content type: `application/json`
   - Secret: Enter the same webhook secret you used in your `.env` file
   - Events: Select "Pull requests" only
   - Active: Check this box
4. Click "Add webhook"

#### Step 4: Test the PR Bot

1. Create a new pull request in your repository that includes code files
2. Watch your PR Bot logs to see the webhook being received
3. The bot should automatically add a code review comment on the first line of code in the first file of the PR

> **Note:** For detailed testing instructions, see the [PR Bot Testing Guide](PR_TESTING.md).

> **Note:** For detailed instructions on installing and running ngrok, including troubleshooting tips, see the [ngrok setup guide](NGROK_SETUP.md).

#### Step 5: Debugging

If the bot doesn't respond:

1. Check the Flask application logs for errors
2. Verify the webhook was received (you should see "Webhook Received" in the logs)
3. Ensure your PAT has the correct permissions
4. Check that the webhook secret matches between GitHub and your `.env` file
5. Verify ngrok is running and the URL is correctly configured in GitHub

## Extending the Bots

You can extend these bots by:

1. Adding more commands to the Issue Bot (modify the bot logic in `issue_bot.py`)
2. Adding more functionality to the PR Bot (modify the bot logic in `pr_bot.py`)
3. Responding to different GitHub events (modify the webhook handlers)
4. Adding more complex interactions with the GitHub API

## Shutting Down

1. Stop both bot applications (Ctrl+C in each terminal)
2. Stop all ngrok instances (Ctrl+C in each ngrok terminal)
3. Deactivate the virtual environment:
   ```bash
   deactivate
   ```

## Security Notes

- Never commit your `.env` file or expose your PAT or webhook secret
- For production use, consider more secure deployment options
- The webhook secret is crucial for verifying that requests come from GitHub
