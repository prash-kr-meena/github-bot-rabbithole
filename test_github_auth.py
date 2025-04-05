#!/usr/bin/env python3
"""
Utility script to test GitHub API authentication using the Personal Access Token.
"""

import os
import sys
from github import Github
from dotenv import load_dotenv

def test_github_authentication():
    """Test GitHub API authentication and display user information."""
    # Load environment variables
    load_dotenv()
    
    # Get GitHub PAT from environment
    github_pat = os.getenv("GITHUB_PAT")
    
    if not github_pat:
        print("ERROR: GITHUB_PAT environment variable not set.")
        print("Please set it in your .env file or provide it as a command-line argument.")
        return False
    
    if github_pat == "YOUR_COPIED_PERSONAL_ACCESS_TOKEN":
        print("ERROR: You need to replace the placeholder with your actual GitHub PAT.")
        print("Edit the .env file and set GITHUB_PAT to your actual token.")
        return False
    
    # Try to authenticate with GitHub
    try:
        g = Github(github_pat)
        user = g.get_user()
        
        # Get rate limit information
        rate_limit = g.get_rate_limit()
        core_rate_limit = rate_limit.core
        
        # Display user information
        print("\nGitHub Authentication Successful!")
        print("================================")
        print(f"Authenticated as: {user.login}")
        print(f"Name: {user.name or 'Not provided'}")
        print(f"Email: {user.email or 'Not provided'}")
        print(f"Organization: {user.company or 'Not provided'}")
        print(f"Location: {user.location or 'Not provided'}")
        print(f"Public Repositories: {user.public_repos}")
        
        # Display rate limit information
        print("\nAPI Rate Limit Information:")
        print(f"Remaining requests: {core_rate_limit.remaining}/{core_rate_limit.limit}")
        print(f"Reset time: {core_rate_limit.reset.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test listing repositories
        print("\nTesting repository access...")
        repos = list(user.get_repos(sort="updated", direction="desc")[:5])
        if repos:
            print("Recently updated repositories:")
            for repo in repos:
                print(f"- {repo.full_name} (Updated: {repo.updated_at.strftime('%Y-%m-%d')})")
        else:
            print("No repositories found or accessible with this token.")
        
        return True
    
    except Exception as e:
        print(f"\nERROR: GitHub authentication failed: {e}")
        print("\nPossible causes:")
        print("1. The token may be invalid or expired")
        print("2. The token may not have the required permissions")
        print("3. There might be network connectivity issues")
        print("\nPlease check your token and try again.")
        return False

if __name__ == "__main__":
    print("GitHub API Authentication Test")
    print("=============================")
    
    # Check if a token was provided as a command-line argument
    if len(sys.argv) > 1:
        os.environ["GITHUB_PAT"] = sys.argv[1]
        print("Using token provided as command-line argument")
    else:
        print("Using token from .env file")
    
    success = test_github_authentication()
    
    if success:
        print("\nYour GitHub PAT is working correctly!")
        print("You can now run the GitHub bot with this token.")
    else:
        print("\nPlease fix the authentication issues before running the bot.")
        sys.exit(1)
