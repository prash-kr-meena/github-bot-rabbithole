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

def check_ngrok_api():
    """Check if ngrok is running by querying its local API."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.ConnectionError:
        return None

def get_ngrok_url():
    """Get the public URL from ngrok if it's running."""
    tunnels_data = check_ngrok_api()
    
    if not tunnels_data or "tunnels" not in tunnels_data or not tunnels_data["tunnels"]:
        return None
    
    # Look for https tunnel
    for tunnel in tunnels_data["tunnels"]:
        if tunnel["proto"] == "https":
            return tunnel["public_url"]
    
    # If no https tunnel, return the first one
    return tunnels_data["tunnels"][0]["public_url"]

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

if __name__ == "__main__":
    print("ngrok Connectivity Test")
    print("======================")
    
    # Check if ngrok is running
    print("Checking if ngrok is running...")
    ngrok_url = get_ngrok_url()
    
    if not ngrok_url:
        print("ngrok is not running or not exposing port 5000.")
        
        # Ask if user wants to start ngrok
        if input("Would you like to attempt to start ngrok? (y/n): ").strip().lower() == 'y':
            if start_ngrok():
                # Check again for the URL
                time.sleep(2)
                ngrok_url = get_ngrok_url()
            else:
                print("\nPlease start ngrok manually with:")
                print("ngrok http 5000")
                sys.exit(1)
        else:
            print("\nPlease start ngrok manually with:")
            print("ngrok http 5000")
            sys.exit(1)
    
    if ngrok_url:
        print(f"\nngrok is running!")
        print(f"Public URL: {ngrok_url}")
        
        # Extract the base URL for the webhook
        webhook_url = f"{ngrok_url}/webhook"
        
        print("\nFor GitHub webhook configuration, use:")
        print(f"Payload URL: {webhook_url}")
        print("Content type: application/json")
        print("Secret: [Your webhook secret from .env]")
        
        # Test the webhook endpoint
        print("\nTesting webhook endpoint connectivity...")
        test_webhook_endpoint(ngrok_url)
        
        print("\nIMPORTANT: ngrok URLs change each time you restart ngrok.")
        print("If you restart ngrok, you'll need to update your GitHub webhook URL.")
    else:
        print("Could not detect ngrok URL even after attempting to start it.")
        print("Please ensure ngrok is installed correctly and try again.")
        sys.exit(1)
