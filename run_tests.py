#!/usr/bin/env python3
"""
Comprehensive test script that runs all the individual test scripts in sequence.
This provides a one-stop testing solution for the GitHub bot.
"""

import os
import sys
import subprocess
import time
import platform

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

def run_command(command, shell=False):
    """Run a command and return its exit code."""
    try:
        if isinstance(command, list) and shell:
            # Convert list to string if shell=True
            command = " ".join(command)
        
        process = subprocess.run(command, shell=shell, check=False)
        return process.returncode
    except Exception as e:
        print(f"Error running command: {e}")
        return 1

def check_environment():
    """Check if the virtual environment is activated."""
    if not os.environ.get("VIRTUAL_ENV"):
        print("WARNING: Virtual environment does not appear to be activated.")
        print("It's recommended to activate your virtual environment first:")
        if platform.system() == "Windows":
            print("  venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return False
    return True

def check_files():
    """Check if all required files exist."""
    required_files = [
        "app.py",
        ".env",
        "requirements.txt",
        "test_github_auth.py",
        "test_ngrok.py",
        "test_bot.py"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("ERROR: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True

def check_test_env_vars():
    """Check if the test environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    repo = os.getenv("GITHUB_REPO", "your-username/your-repo")
    username = os.getenv("GITHUB_USERNAME", "your-username")
    
    if repo == "your-username/your-repo" or username == "your-username":
        print("\n⚠️  WARNING: Using placeholder values for GitHub repository or username!")
        print("The webhook test may fail with a 404 error when trying to interact with the GitHub API.")
        print("Please set the following environment variables in your .env file:")
        print("  GITHUB_REPO=your-actual-username/your-actual-repo")
        print("  GITHUB_ISSUE_NUMBER=1  # Use an actual issue number in your repo")
        print("  GITHUB_USERNAME=your-actual-username")
        print("\nSee TESTING.md for more information on fixing this issue.")
        
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return False
    
    return True

def test_github_auth():
    """Run the GitHub authentication test."""
    print_header("Testing GitHub Authentication")
    # Use direct module import and execution instead of subprocess
    try:
        # Import the module
        import test_github_auth
        # Run the test function
        success = test_github_auth.test_github_authentication()
        return 0 if success else 1
    except Exception as e:
        print(f"Error running GitHub authentication test: {e}")
        return 1

def test_ngrok():
    """Run the ngrok connectivity test."""
    print_header("Testing ngrok Connectivity")
    # Use direct module import and execution instead of subprocess
    try:
        # Check if ngrok is running using functions from test_ngrok.py
        import test_ngrok
        ngrok_url = test_ngrok.get_ngrok_url()
        
        if ngrok_url:
            print(f"ngrok is running!")
            print(f"Public URL: {ngrok_url}")
            print("\nFor GitHub webhook configuration, use:")
            print(f"Payload URL: {ngrok_url}/webhook")
            return 0
        else:
            print("ngrok is not running or not exposing port 5000.")
            print("Please start ngrok with: ngrok http 5000")
            return 1
    except Exception as e:
        print(f"Error running ngrok test: {e}")
        return 1

def test_flask_app():
    """Test if the Flask app can start."""
    print_header("Testing Flask Application")
    
    print("Starting Flask application in test mode...")
    
    # Use a different approach based on the operating system
    if platform.system() == "Windows":
        flask_process = subprocess.Popen(
            [sys.executable, "app.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # For macOS/Linux, start in background
        flask_process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    # Give the Flask app time to start
    print("Waiting for Flask app to start...")
    time.sleep(3)
    
    # Check if the process is still running
    if flask_process.poll() is None:
        print("Flask application started successfully!")
        
        # Ask if user wants to keep it running
        keep_running = input("Keep Flask app running for webhook tests? (y/n): ").strip().lower()
        
        if keep_running != 'y':
            print("Stopping Flask application...")
            flask_process.terminate()
            return 0
        else:
            print("Flask application will continue running in the background.")
            print("Remember to stop it manually when you're done testing.")
            return 0
    else:
        print("ERROR: Flask application failed to start.")
        return 1

def test_webhook():
    """Run the webhook simulation test."""
    print_header("Testing Webhook Simulation")
    
    # Check if Flask app is running on port 5000
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 5000))
    sock.close()
    
    if result != 0:
        print("ERROR: Flask application is not running on port 5000.")
        print("Please start the Flask application first with:")
        print("  python app.py")
        return 1
    
    try:
        # Import the test_bot module and run its functions directly
        import test_bot
        
        print("GitHub Bot Test Script")
        print("=====================")
        print(f"Bot URL: {test_bot.BOT_URL}")
        print(f"Repository: {test_bot.REPO_FULL_NAME}")
        print(f"Issue Number: {test_bot.ISSUE_NUMBER}")
        print(f"Commenter: {test_bot.COMMENTER_LOGIN}")
        print("=====================")
        
        # First, test if the server is running
        try:
            root_response = test_bot.requests.get("http://localhost:5000/")
            print(f"Server status: {root_response.status_code} - {root_response.text.strip()}")
        except test_bot.requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to the bot server. Make sure it's running on http://localhost:5000")
            return 1
        
        print("\n1. Testing ping event...")
        test_bot.test_ping_event()
        
        print("\n2. Testing /greet command...")
        test_bot.simulate_issue_comment_event("/greet")
        
        print("\n3. Testing non-command comment...")
        test_bot.simulate_issue_comment_event("This is a regular comment, not a command.")
        
        print("\nTests completed. Check the bot's console output for more details.")
        return 0
    except Exception as e:
        print(f"Error running webhook test: {e}")
        return 1

def main():
    """Run all tests in sequence."""
    print_header("GitHub Bot Comprehensive Test Suite")
    
    # Check environment and files
    if not check_environment() or not check_files() or not check_test_env_vars():
        return 1
    
    # Run tests in sequence, stopping if any fail
    tests = [
        ("GitHub Authentication", test_github_auth),
        ("ngrok Connectivity", test_ngrok),
        ("Flask Application", test_flask_app),
        ("Webhook Simulation", test_webhook)
    ]
    
    results = {}
    
    for name, test_func in tests:
        print(f"\nRunning {name} test...")
        result = test_func()
        results[name] = "PASSED" if result == 0 else "FAILED"
        
        if result != 0:
            print(f"\n{name} test failed. Stopping test suite.")
            break
    
    # Print summary
    print_header("Test Results Summary")
    
    for name, status in results.items():
        print(f"{name}: {status}")
    
    if all(status == "PASSED" for status in results.values()):
        print("\nAll tests passed! Your GitHub bot setup is working correctly.")
        return 0
    else:
        print("\nSome tests failed. Please fix the issues and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
