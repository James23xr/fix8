import os
import sys
import json
import uuid

# Add the parent directory to the path so we can import src.core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, session, request, jsonify, send_from_directory
from flask_session import Session
import pandas as pd

from src.core import Fix8Core

app = Flask(__name__, static_folder='static', static_url_path='')

# Configure server-side session
app.config['SECRET_KEY'] = 'super-secret-fix8-key-for-dev'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), '.flask_sessions')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Create temp session folder
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize Session
Session(app)

# In-memory session store (mapping session_id to Fix8Core instance)
# This avoids pickling complex pandas/numpy structures to disk in development.
ACTIVE_SESSIONS = {}

def get_engine():
    """Retrieve or create the Fix8Core engine for the current session."""
    # Generate an ID if this session is new
    if 'uid' not in session:
        session['uid'] = str(uuid.uuid4())
        
    uid = session['uid']
    if uid not in ACTIVE_SESSIONS:
        # Initialize a fresh core engine for this specific user
        ACTIVE_SESSIONS[uid] = Fix8Core()
        print(f"[*] Initialized new Fix8Core engine for session: {uid}")
        
    return ACTIVE_SESSIONS[uid]


# ---------------------------------------------------------
# ROUTES: Static Files
# ---------------------------------------------------------
@app.route('/')
def index():
    return app.send_static_file('index.html')


# ---------------------------------------------------------
# API ROUTES: Core Logic Wrapper
# ---------------------------------------------------------
# (Endpoints to be implemented in subsequent PRs)



if __name__ == '__main__':
    print("Fix8 Web Server Starting...")
    print("Serving from:", os.path.dirname(os.path.abspath(__file__)))
    app.run(debug=True, port=5000)
