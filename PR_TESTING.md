# Testing the GitHub PR Bot with AI Code Review

This document provides instructions for testing the GitHub PR Bot, which automatically adds AI-powered code review comments to pull requests.

## Prerequisites

Before testing the PR bot, ensure you have:

1. A GitHub account
2. A GitHub repository where you have admin permissions
3. A GitHub Personal Access Token (PAT) with appropriate permissions
4. ngrok installed for exposing your local server to the internet

## Setup

### 1. Environment Variables

Create or update your `.env` file with the following variables:

```
# GitHub Authentication
GITHUB_PAT=your_personal_access_token
WEBHOOK_SECRET=your_webhook_secret

# Repository Information
GITHUB_REPO=your-username/your-repo
GITHUB_PR_NUMBER=1  # An actual PR number in your repository
GITHUB_USERNAME=your-username

# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_BASE_URL=https://api.rabbithole.cred.club
ANTHROPIC_MODEL=claude-3-7-sonnet-20250219
```

Replace the placeholder values with your actual information:
- `GITHUB_PAT`: Your GitHub Personal Access Token
- `WEBHOOK_SECRET`: A secret string used to verify webhook payloads
- `GITHUB_REPO`: The full name of your repository (username/repo-name)
- `GITHUB_PR_NUMBER`: The number of an existing pull request in your repository
- `GITHUB_USERNAME`: Your GitHub username
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `ANTHROPIC_BASE_URL`: The base URL for the Anthropic API (default is provided)
- `ANTHROPIC_MODEL`: The Anthropic model to use for code reviews (default is provided)

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configure GitHub Webhook

1. Start ngrok to expose your local server:
   ```bash
   ngrok http 5001
   ```

2. Note the public URL provided by ngrok (e.g., `https://abcd1234.ngrok.io`)

3. In your GitHub repository, go to Settings > Webhooks > Add webhook:
   - Payload URL: `https://your-ngrok-url/webhook`
   - Content type: `application/json`
   - Secret: The same value as `WEBHOOK_SECRET` in your `.env` file
   - Events: Select "Pull requests"
   - Active: Checked

## Running the PR Bot

Start the PR bot with:

```bash
python pr_bot.py
```

The bot will run on `http://localhost:5001` and listen for webhook events from GitHub.

## Testing

### Automated Testing

Run the automated test script:

```bash
python test_pr_bot.py
```

This script simulates:
1. A ping event to verify the webhook endpoint
2. A PR opened event to test the bot's ability to add review comments

### Manual Testing

To test the bot manually:

1. Ensure the PR bot is running (`python pr_bot.py`)
2. Create a new pull request in your GitHub repository
3. The bot should automatically add a review comment on the first line of code in the first file of the PR

## Understanding the Results

### Successful Test

If the test is successful:
- The ping event should return a 200 status code
- The PR opened event should return a 200 status code
- The bot should post a review comment on the first line of code in the PR

### Common Issues

1. **404 Not Found Error**:
   - Ensure your `GITHUB_REPO` and `GITHUB_PR_NUMBER` are correct
   - Verify that your GitHub PAT has the necessary permissions

2. **401 Unauthorized Error**:
   - Check that your `GITHUB_PAT` is valid and has not expired
   - Ensure the PAT has the necessary permissions (repo scope)

3. **Signature Verification Failed**:
   - Ensure the `WEBHOOK_SECRET` in your `.env` file matches the one configured in GitHub

4. **No Review Comment Added**:
   - Check the bot's console output for error messages
   - Verify that the PR contains files with actual code (not just documentation or empty files)

## How It Works

The PR bot with AI code review:

1. **Webhook Processing**:
   - Receives a webhook event when a PR is opened
   - Verifies the webhook signature
   - Extracts PR information (title, description, author, etc.)

2. **Repository Analysis**:
   - Clones the repository to a local `.repos` directory
   - Fetches the list of files changed in the PR
   - For each file, gets both the full content and the specific changes (diff)

3. **AI Code Review**:
   - Sends the file content and changes to the Anthropic API
   - Provides a comprehensive prompt with code review guidelines
   - Receives an AI-generated code review with suggestions and feedback

4. **Review Comments**:
   - Posts review comments on specific sections of code that were changed
   - Each comment includes the AI-generated review for that file
   - Posts a summary comment with an overview of the review process

5. **Testing**:
   - The `test_pr_bot.py` script provides several test options:
     - Ping event test: Verifies the webhook endpoint
     - PR opened event test: Tests the full PR review process
     - Repository cloning test: Tests the repository cloning functionality
     - AI code review test: Tests the AI code review generation

The bot uses a temporary directory to store cloned repositories, which allows it to analyze the code in its full context rather than just the isolated changes. This provides more comprehensive and accurate code reviews.
