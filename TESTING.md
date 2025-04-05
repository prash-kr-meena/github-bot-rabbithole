# Testing the GitHub Bot

This document provides detailed information about testing the GitHub bot and troubleshooting common issues.

## Understanding the Test Script

The `test_bot.py` script simulates GitHub webhook events to test the bot locally. It sends three types of events:

1. A ping event (to verify the webhook endpoint is working)
2. An issue comment event with the "/greet" command
3. An issue comment event with a regular comment (not a command)

## Fixing the Failed Test

If you're seeing a 500 error with a message like:
```
Failed to interact with GitHub API: 404 {"message": "Not Found", "documentation_url": "https://docs.github.com/rest/repos/repos#get-a-repository", "status": "404"}
```

This is likely because the test script is using placeholder values for the repository name, issue number, and username.

### Solution

Update your `.env` file to include the following variables with your actual GitHub information:

```
# Test configuration - Replace with your actual GitHub information
GITHUB_REPO=your-actual-username/your-actual-repo
GITHUB_ISSUE_NUMBER=1
GITHUB_USERNAME=your-actual-username
```

Replace:
- `your-actual-username/your-actual-repo` with your actual GitHub username and repository name
- `1` with an actual issue number that exists in your repository
- `your-actual-username` with your actual GitHub username

The test script will use these environment variables when simulating webhook events.

## How the Test Script Works

1. The script loads environment variables from your `.env` file
2. It creates a simulated webhook payload with your repository, issue, and username information
3. It signs the payload with your webhook secret
4. It sends the payload to your local bot server
5. It checks the response to verify that the bot handled the event correctly

## Common Issues

### 404 Not Found Error

This occurs when the bot tries to interact with a GitHub repository that doesn't exist. Make sure:
- You've set the `GITHUB_REPO` environment variable to a real repository that you own
- The repository name is spelled correctly
- Your GitHub Personal Access Token (PAT) has access to this repository

### 401 Unauthorized Error

This occurs when your GitHub PAT is invalid or doesn't have the necessary permissions. Make sure:
- Your PAT is correct and hasn't expired
- Your PAT has the `repo` scope (or at least `issues:write` for this specific bot)

### 422 Unprocessable Entity Error

This can occur if you're trying to create a comment on an issue that doesn't exist. Make sure:
- You've set the `GITHUB_ISSUE_NUMBER` environment variable to a real issue in your repository
- The issue is open (not closed)

## Running Tests

To run the tests:

```bash
# Make sure your bot server is running
python app.py

# In another terminal, run the test script
python test_bot.py
```

You should see output indicating whether each test passed or failed.
