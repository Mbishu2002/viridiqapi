#!/usr/bin/env python

import subprocess
import time
from pyngrok import ngrok

# Replace with your Django project's manage.py path if needed
DJANGO_MANAGE_PATH = 'manage.py'
PORT = 8000  # Default Django port

def start_django_server():
    """Start the Django development server."""
    print(f"Starting Django development server on port {PORT}...")
    # Run the Django server in a subprocess
    process = subprocess.Popen(["python", DJANGO_MANAGE_PATH, "runserver", f"0.0.0.0:{PORT}"])
    return process

def start_ngrok_tunnel(port):
    """Start ngrok tunnel and return the public URL."""
    print(f"Starting ngrok on port {port}...")
    # Start ngrok tunnel
    public_url = ngrok.connect(port)
    return public_url

def main():
    # Configure ngrok with the authtoken (if required)
    # ngrok.set_auth_token('your_ngrok_authtoken_here')
    
    # Start Django server
    django_process = start_django_server()

    # Give Django some time to start
    time.sleep(5)

    # Start ngrok tunnel
    public_url = start_ngrok_tunnel(PORT)
    print(f"ngrok is forwarding to: {public_url}")

    try:
        # Keep the script running to keep the server and ngrok tunnel open
        print("Press Ctrl+C to stop the server and ngrok.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server and ngrok...")
        # Terminate the Django server
        django_process.terminate()
        # Disconnect ngrok
        ngrok.disconnect(public_url)

if __name__ == "__main__":
    main()
