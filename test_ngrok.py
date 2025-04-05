#!/usr/bin/env python3
"""
Utility script to test ngrok connectivity and get the public URL.
This helps verify that ngrok is running correctly before setting up GitHub webhooks.
"""

import requests
import json
import sys
import time
import subprocess
import os
import platform

def check_ngrok_api(api_port=4040):
    """Check if ngrok is running by querying its local API."""
    try:
        response = requests.get(f"http://localhost:{api_port}/api/tunnels")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.ConnectionError:
        return None

def get_ngrok_url(port=5000):
    """Get the public URL from ngrok if it's running.
    
    Args:
        port: The local port that ngrok is forwarding (default: 5000)
    
    Returns:
        The public URL or None if not found
    """
    # Try the default ngrok API port first
    tunnels_data = check_ngrok_api(4040)
    
    # If not found, try alternative API ports (ngrok uses incremental ports for multiple instances)
    if not tunnels_data:
        for api_port in range(4041, 4045):
            tunnels_data = check_ngrok_api(api_port)
            if tunnels_data:
                break
    
    if not tunnels_data or "tunnels" not in tunnels_data or not tunnels_data["tunnels"]:
        return None
    
    # Look for https tunnel for the specified port
    for tunnel in tunnels_data["tunnels"]:
        # Check if this tunnel is forwarding to our target port
        if f"localhost:{port}" in tunnel["config"]["addr"] and tunnel["proto"] == "https":
            return tunnel["public_url"]
    
    # If no https tunnel for our port, try http
    for tunnel in tunnels_data["tunnels"]:
        if f"localhost:{port}" in tunnel["config"]["addr"]:
            return tunnel["public_url"]
    
    # If we couldn't find a tunnel for our specific port, return None
    return None

def test_webhook_endpoint(ngrok_url):
    """Test if the webhook endpoint is accessible through ngrok."""
    webhook_url = f"{ngrok_url}/webhook"
    
    print(f"Testing webhook endpoint: {webhook_url}")
    
    try:
        # Send a simple GET request (our webhook only accepts POST, but this tests connectivity)
        response = requests.get(webhook_url, timeout=5)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 405:  # Method Not Allowed
            print("Received 'Method Not Allowed' response - this is expected since webhooks require POST")
            print("Connectivity test SUCCESSFUL: Your webhook endpoint is accessible through ngrok")
            return True
        else:
            print(f"Received unexpected status code: {response.status_code}")
            print("This might still be okay if your webhook endpoint returns a different status for GET requests")
            return True
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to webhook endpoint: {e}")
        return False

def start_ngrok():
    """Attempt to start ngrok if it's not running."""
    system = platform.system()
    
    if system == "Windows":
        cmd = "start ngrok http 5000"
        shell = True
    else:  # macOS or Linux
        cmd = "ngrok http 5000"
        shell = True
    
    try:
        print("Attempting to start ngrok...")
        subprocess.Popen(cmd, shell=shell)
        
        # Wait for ngrok to start
        for _ in range(5):
            time.sleep(2)
            if check_ngrok_api():
                print("ngrok started successfully!")
                return True
        
        print("Failed to start ngrok automatically.")
        return False
    except Exception as e:
        print(f"Error starting ngrok: {e}")
        return False

def start_ngrok_for_port(port):
    """Attempt to start ngrok for a specific port if it's not running."""
    system = platform.system()
    
    if system == "Windows":
        cmd = f"start ngrok http {port}"
        shell = True
    else:  # macOS or Linux
        cmd = f"ngrok http {port}"
        shell = True
    
    try:
        print(f"Attempting to start ngrok for port {port}...")
        subprocess.Popen(cmd, shell=shell)
        
        # Wait for ngrok to start
        for _ in range(5):
            time.sleep(2)
            if get_ngrok_url(port):
                print(f"ngrok started successfully for port {port}!")
                return True
        
        print(f"Failed to start ngrok automatically for port {port}.")
        return False
    except Exception as e:
        print(f"Error starting ngrok: {e}")
        return False

if __name__ == "__main__":
    print("ngrok Connectivity Test")
    print("======================")
    
    # Check if ngrok is running for Issue Bot (port 5000)
    print("Checking if ngrok is running for Issue Bot (port 5000)...")
    issue_bot_url = get_ngrok_url(5000)
    
    if not issue_bot_url:
        print("ngrok is not running or not exposing port 5000 for Issue Bot.")
        
        # Ask if user wants to start ngrok
        if input("Would you like to attempt to start ngrok for Issue Bot? (y/n): ").strip().lower() == 'y':
            if start_ngrok_for_port(5000):
                # Check again for the URL
                time.sleep(2)
                issue_bot_url = get_ngrok_url(5000)
            else:
                print("\nPlease start ngrok manually with:")
                print("ngrok http 5000")
        else:
            print("\nPlease start ngrok manually with:")
            print("ngrok http 5000")
    
    # Check if ngrok is running for PR Bot (port 5001)
    print("\nChecking if ngrok is running for PR Bot (port 5001)...")
    pr_bot_url = get_ngrok_url(5001)
    
    if not pr_bot_url:
        print("ngrok is not running or not exposing port 5001 for PR Bot.")
        
        # Ask if user wants to start ngrok
        if input("Would you like to attempt to start ngrok for PR Bot? (y/n): ").strip().lower() == 'y':
            if start_ngrok_for_port(5001):
                # Check again for the URL
                time.sleep(2)
                pr_bot_url = get_ngrok_url(5001)
            else:
                print("\nPlease start ngrok manually with:")
                print("ngrok http 5001")
        else:
            print("\nPlease start ngrok manually with:")
            print("ngrok http 5001")
    
    # Display results for Issue Bot
    if issue_bot_url:
        print(f"\nngrok is running for Issue Bot!")
        print(f"Public URL: {issue_bot_url}")
        
        # Extract the base URL for the webhook
        webhook_url = f"{issue_bot_url}/webhook"
        
        print("\nFor Issue Bot webhook configuration, use:")
        print(f"Payload URL: {webhook_url}")
        print("Content type: application/json")
        print("Secret: [Your webhook secret from .env]")
        print("Events: Issue comments")
        
        # Test the webhook endpoint
        print("\nTesting Issue Bot webhook endpoint connectivity...")
        test_webhook_endpoint(issue_bot_url)
    
    # Display results for PR Bot
    if pr_bot_url:
        print(f"\nngrok is running for PR Bot!")
        print(f"Public URL: {pr_bot_url}")
        
        # Extract the base URL for the webhook
        webhook_url = f"{pr_bot_url}/webhook"
        
        print("\nFor PR Bot webhook configuration, use:")
        print(f"Payload URL: {webhook_url}")
        print("Content type: application/json")
        print("Secret: [Your webhook secret from .env]")
        print("Events: Pull requests")
        
        # Test the webhook endpoint
        print("\nTesting PR Bot webhook endpoint connectivity...")
        test_webhook_endpoint(pr_bot_url)
    
    if issue_bot_url or pr_bot_url:
        print("\nIMPORTANT: ngrok URLs change each time you restart ngrok.")
        print("If you restart ngrok, you'll need to update your GitHub webhook URLs.")
        sys.exit(0)
    else:
        print("\nCould not detect any ngrok URLs even after attempting to start them.")
        print("Please ensure ngrok is installed correctly and try again.")
        sys.exit(1)
