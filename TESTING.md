# Testing Guide for GitHub Bot

This guide provides detailed instructions for testing your GitHub bot locally using two different approaches:

1. **Local Testing with Simulation Script**: Test without GitHub integration
2. **End-to-End Testing with ngrok**: Test with actual GitHub webhooks

## Method 1: Local Testing with Simulation Script

This method allows you to test your bot's functionality without setting up GitHub webhooks. It's useful for initial development and debugging.

### Prerequisites

- Bot code is set up correctly
- `.env` file is configured with a webhook secret (the GitHub PAT is not needed for this test)

### Steps

1. **Start the Flask Application**

   In your terminal:

   ```bash
   # Make sure you're in the project directory
   cd simple-github-bot-local
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   # Start the Flask app
   python app.py
   ```

   You should see output indicating the server is running on http://localhost:5000.

2. **Configure the Test Script**

   Open `test_bot.py` and update the following variables:

   ```python
   REPO_FULL_NAME = "your-username/your-repo"  # Replace with any valid repo name
   ISSUE_NUMBER = 1  # Any number will work for testing
   COMMENTER_LOGIN = "your-username"  # Replace with any username
   ```

3. **Run the Test Script**

   In a new terminal window:

   ```bash
   # Make sure you're in the project directory
   cd simple-github-bot-local
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   # Run the test script
   python test_bot.py
   ```

4. **Analyze the Results**

   The test script will:
   - Check if the server is running
   - Send a simulated ping event
   - Send a simulated issue comment with `/greet`
   - Send a simulated issue comment with regular text

   Watch both the test script output and the Flask application logs to see how the bot responds to each event.

## Method 2: End-to-End Testing with GitHub Webhooks

This method tests the complete workflow with actual GitHub webhooks, providing a more realistic test environment.

### Prerequisites

- GitHub account
- A repository you own (for testing)
- GitHub Personal Access Token (PAT) with appropriate permissions
- ngrok installed and configured

### Steps

1. **Configure Environment Variables**

   Ensure your `.env` file has both the GitHub PAT and webhook secret:

   ```
   GITHUB_PAT=your_actual_personal_access_token
   WEBHOOK_SECRET=your_webhook_secret
   ```

2. **Start the Flask Application**

   ```bash
   # Make sure you're in the project directory
   cd simple-github-bot-local
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   # Start the Flask app
   python app.py
   ```

3. **Start ngrok**

   In a new terminal window:

   ```bash
   # Start ngrok on port 5000
   ngrok http 5000
   ```

   ngrok will display a forwarding URL (e.g., `https://a1b2c3d4.ngrok.io`). Copy this URL.

4. **Configure GitHub Webhook**

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

5. **Test with Real GitHub Interactions**

   1. Create a new issue in your repository
   2. Add a comment with just `/greet` in the body
   3. Watch your Flask application logs to see the webhook being received
   4. Refresh the GitHub issue page to see if the bot replied with a greeting

6. **Verify Authentication**

   When your bot starts, it should print a message confirming successful authentication with GitHub:

   ```
   Successfully authenticated with GitHub as: your-username
   ```

   If you don't see this message or see an error instead, check your PAT configuration.

## Troubleshooting

### Common Issues and Solutions

1. **Flask App Not Starting**
   - Check for syntax errors in your code
   - Ensure all required packages are installed
   - Verify environment variables are set correctly

2. **Webhook Signature Verification Failing**
   - Ensure the webhook secret in GitHub matches exactly with your `.env` file
   - Check for any whitespace or encoding issues in the secret

3. **Bot Not Responding to Commands**
   - Verify the command format is exactly as expected (`/greet`)
   - Check the Flask logs for any errors in processing the command
   - Ensure the PAT has sufficient permissions to post comments

4. **ngrok Connection Issues**
   - Restart ngrok if the tunnel expires
   - Ensure you're using the latest ngrok URL in your webhook configuration
   - Check ngrok logs for any connection errors

5. **GitHub API Rate Limiting**
   - If you see rate limiting errors, wait for the rate limit to reset
   - Consider using a different PAT if available

### Debugging Tips

1. **Enable Detailed Payload Logging**

   In `app.py`, uncomment this line to see the full webhook payload:

   ```python
   print(json.dumps(payload, indent=2))  # Uncomment for detailed payload view
   ```

2. **Test API Authentication Separately**

   Create a simple script to test GitHub API access:

   ```python
   from github import Github
   import os
   from dotenv import load_dotenv

   load_dotenv()
   token = os.getenv("GITHUB_PAT")
   g = Github(token)
   user = g.get_user()
   print(f"Authenticated as: {user.login}")
   print(f"Rate limit remaining: {g.get_rate_limit().core.remaining}")
   ```

3. **Verify Webhook Delivery in GitHub**

   GitHub's webhook settings page shows recent deliveries and their status. Use this to confirm if webhooks are being sent and what response GitHub is receiving.

## Next Steps After Successful Testing

Once your bot is working correctly:

1. **Add More Commands**: Extend the bot's functionality with additional commands
2. **Improve Error Handling**: Add more robust error handling and logging
3. **Consider Deployment Options**: For a production bot, consider deploying to a cloud service
