# Testing the PR Bot

This document provides detailed information about testing the GitHub PR bot and troubleshooting common issues.

## Understanding the PR Bot

The PR bot is designed to automatically add a comment to pull requests when they are opened. It listens for the `pull_request` event with the `opened` action and adds a comment saying "PR Comment by Bot" to the PR.

## Testing the PR Bot Locally

### Prerequisites

Before testing the PR bot, make sure you have:

1. Set up your environment variables in the `.env` file:
   ```
   GITHUB_PAT=your-personal-access-token
   WEBHOOK_SECRET=your-webhook-secret
   GITHUB_REPO=your-username/your-repo
   GITHUB_PR_NUMBER=1
   GITHUB_USERNAME=your-username
   ```

2. Installed all required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the PR Bot

1. Start the PR bot:
   ```bash
   python pr_bot.py
   ```

2. In a separate terminal, start ngrok to expose your local server:
   ```bash
   ngrok http 5001
   ```

3. Configure a GitHub webhook for your repository:
   - Payload URL: `https://your-ngrok-url/webhook`
   - Content type: `application/json`
   - Secret: The same webhook secret from your `.env` file
   - Events: Select "Pull requests" only

### Testing with the Test Script

You can use the `test_pr_bot.py` script to simulate a PR opened event without actually creating a PR on GitHub:

```bash
python test_pr_bot.py
```

This script will:
1. Send a simulated ping event to verify the webhook endpoint is working
2. Send a simulated PR opened event to test the bot's functionality

## Common Issues

### 404 Not Found Error

This occurs when the bot tries to interact with a GitHub repository or PR that doesn't exist. Make sure:
- You've set the `GITHUB_REPO` environment variable to a real repository that you own
- The repository name is spelled correctly
- Your GitHub Personal Access Token (PAT) has access to this repository
- If testing with a real PR, make sure the `GITHUB_PR_NUMBER` corresponds to an actual PR in your repository

### 401 Unauthorized Error

This occurs when your GitHub PAT is invalid or doesn't have the necessary permissions. Make sure:
- Your PAT is correct and hasn't expired
- Your PAT has the `repo` scope (or at least `pull_requests:write` for this specific bot)

### Webhook Not Triggering

If your webhook isn't triggering when you create a new PR:
1. Check that ngrok is running and the URL is correctly configured in GitHub
2. Verify that you selected "Pull requests" in the webhook events
3. Check the webhook secret matches between GitHub and your `.env` file
4. Look at the webhook deliveries in GitHub to see if there are any errors

## Extending the PR Bot

You can extend the PR bot by:

1. Adding more actions to respond to (e.g., `synchronize`, `closed`, `reopened`)
2. Customizing the comment message
3. Adding more complex logic, such as checking PR contents or labels
4. Integrating with other services or APIs

To modify the bot's behavior, edit the `pr_bot.py` file and update the webhook handler function.
