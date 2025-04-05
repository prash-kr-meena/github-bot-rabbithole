# Installing and Running ngrok

This guide provides step-by-step instructions for installing and running ngrok on different operating systems.

## What is ngrok?

ngrok is a tool that creates secure tunnels to expose your local web server to the internet. It's essential for our GitHub bot because it allows GitHub to send webhook events to your local machine.

## Installation Instructions

### macOS

#### Option 1: Using Homebrew (Recommended)

1. If you don't have Homebrew installed, install it first:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install ngrok using Homebrew:
   ```bash
   brew install ngrok
   ```

#### Option 2: Manual Installation

1. Go to [ngrok.com/download](https://ngrok.com/download)
2. Download the macOS version (ZIP file)
3. Extract the ZIP file
4. Move the ngrok executable to a directory in your PATH:
   ```bash
   mv ngrok /usr/local/bin/
   ```

### Windows

#### Option 1: Using Chocolatey

1. If you don't have Chocolatey installed, install it first by following the instructions at [chocolatey.org/install](https://chocolatey.org/install)
2. Open Command Prompt or PowerShell as Administrator
3. Install ngrok:
   ```
   choco install ngrok
   ```

#### Option 2: Manual Installation

1. Go to [ngrok.com/download](https://ngrok.com/download)
2. Download the Windows version (ZIP file)
3. Extract the ZIP file to a location of your choice (e.g., `C:\ngrok`)
4. Add the ngrok directory to your PATH:
   - Right-click on "This PC" or "My Computer" and select "Properties"
   - Click on "Advanced system settings"
   - Click on "Environment Variables"
   - Under "System variables", find the "Path" variable, select it and click "Edit"
   - Click "New" and add the path to the ngrok directory (e.g., `C:\ngrok`)
   - Click "OK" on all dialogs to save the changes

### Linux

#### Option 1: Using Package Manager

For Debian/Ubuntu:
```bash
sudo apt update
sudo apt install snapd
sudo snap install ngrok
```

For other distributions, check if ngrok is available in your package manager.

#### Option 2: Manual Installation

1. Go to [ngrok.com/download](https://ngrok.com/download)
2. Download the Linux version (ZIP file)
3. Extract the ZIP file:
   ```bash
   unzip ngrok-stable-linux-amd64.zip
   ```
4. Move the ngrok executable to a directory in your PATH:
   ```bash
   sudo mv ngrok /usr/local/bin/
   ```

## Setting Up ngrok

### 1. Create an ngrok Account

1. Go to [ngrok.com](https://ngrok.com/) and sign up for a free account
2. After signing up, log in to your ngrok dashboard

### 2. Get Your Authtoken

1. In your ngrok dashboard, find your authtoken (it should be displayed prominently)
2. Copy the authtoken

### 3. Configure ngrok with Your Authtoken

Run the following command, replacing `YOUR_AUTHTOKEN` with your actual authtoken:

```bash
ngrok authtoken YOUR_AUTHTOKEN
```

This will save your authtoken to the ngrok configuration file.

## Running ngrok

### Basic Usage

To expose a local web server running on port 5000 (the default port for our Flask app):

```bash
ngrok http 5000
```

This will start ngrok and display information about the tunnel, including the public URL that can be used to access your local server.

### Example Output

```
ngrok                                                                                                                                                                                                                  (Ctrl+C to quit)
                                                                                                                                                                                                                                       
Session Status                online                                                                                                                                                                                                   
Account                       Your Name (Plan: Free)                                                                                                                                                                                   
Version                       3.3.1                                                                                                                                                                                                    
Region                        United States (us)                                                                                                                                                                                       
Latency                       24ms                                                                                                                                                                                                     
Web Interface                 http://127.0.0.1:4040                                                                                                                                                                                    
Forwarding                    https://abcd-123-456-789-0.ngrok-free.app -> http://localhost:5000                                                                                                                                       
                                                                                                                                                                                                                                       
Connections                   ttl     opn     rt1     rt5     p50     p90                                                                                                                                                              
                              0       0       0.00    0.00    0.00    0.00
```

### Important Notes

1. **The URL Changes Each Time**: Every time you restart ngrok, you'll get a new URL. You'll need to update your GitHub webhook URL accordingly.

2. **Web Interface**: ngrok provides a web interface at http://localhost:4040 where you can inspect the requests and responses going through the tunnel.

3. **Free Plan Limitations**: The free plan has some limitations, including:
   - Sessions expire after a few hours
   - Limited number of connections per minute
   - No custom subdomains

4. **Keeping ngrok Running**: Keep the terminal window with ngrok running open while you're testing your bot. If you close it, the tunnel will be closed.

## Using ngrok with Our GitHub Bot

1. Start your Flask application:
   ```bash
   python app.py
   ```

2. In a new terminal window, start ngrok:
   ```bash
   ngrok http 5000
   ```

3. Copy the HTTPS URL from the ngrok output (e.g., `https://abcd-123-456-789-0.ngrok-free.app`)

4. Configure your GitHub webhook with this URL, adding `/webhook` at the end:
   ```
   https://abcd-123-456-789-0.ngrok-free.app/webhook
   ```

5. Use the same webhook secret in both your GitHub webhook configuration and your `.env` file

## Troubleshooting

### "command not found" Error

If you get a "command not found" error when trying to run ngrok, it means ngrok is not in your PATH. Try:

1. Running ngrok with the full path to the executable
2. Adding the directory containing ngrok to your PATH
3. Reinstalling ngrok using one of the methods above

### Connection Refused

If you see a "connection refused" error, make sure:

1. Your Flask application is running on port 5000
2. You're using the correct port number in the ngrok command
3. There are no firewalls blocking the connection

### Authtoken Issues

If you see an error about an invalid or missing authtoken:

1. Make sure you've signed up for an ngrok account
2. Run `ngrok authtoken YOUR_AUTHTOKEN` with your actual authtoken
3. Check that the authtoken was saved correctly in the ngrok configuration file

### Rate Limiting

If you're experiencing rate limiting issues:

1. Wait a few minutes before trying again
2. Consider upgrading to a paid plan if you need more connections
3. Make sure you're not making too many requests in a short period of time

## Additional Resources

- [ngrok Documentation](https://ngrok.com/docs)
- [ngrok Status Page](https://status.ngrok.com/)
- [ngrok Support](https://ngrok.com/support)
