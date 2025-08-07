from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    """This route is pinged by an uptime service to keep the bot alive."""
    return "Bot is alive!"

def run():
    """Runs the Flask server."""
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Starts the Flask server in a new thread."""
    server_thread = Thread(target=run)
    server_thread.start()
    print("Keep-alive server starte
    d.")
