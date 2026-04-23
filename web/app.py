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
@app.route('/api/load_demo', methods=['POST'])
def api_load_demo():
    """Phase 1 Hybrid File Handling: Load a demo dataset on the server."""
    engine = get_engine()
    
    # We will pick a demo file. You must make sure a demo file exists at this path.
    # We will place a sample in web/demo_data/
    demo_path = os.path.join(os.path.dirname(__file__), 'demo_data', 'demo_trial.json')
    
    if not os.path.exists(demo_path):
        return jsonify({"error": f"Demo file not found at {demo_path}"}), 404
        
    try:
        with open(demo_path, 'r', encoding='utf-8') as f:
            trial_data = json.load(f)
            
        x_cord, y_cord, duration = [], [], []
        
        # Parse logic ported from batch_processor.py
        if 'fixations' not in trial_data.keys():
            for key in trial_data:
                x_cord.append(trial_data[key][0])
                y_cord.append(trial_data[key][1])
                duration.append(trial_data[key][2])
        else:
            for fixation in trial_data["fixations"]:
                x_cord.append(fixation[0])
                y_cord.append(fixation[1])
                duration.append(fixation[2])
                
        eye_events = pd.DataFrame({
            "x_cord": x_cord,
            "y_cord": y_cord,
            "duration": duration,
            "eye_event": "fixation"
        })
        
        # Inject into engine instance
        engine.eye_events = eye_events
        engine.trial_path = demo_path
        
        # Return state to frontend
        return jsonify({
            "message": "Demo data loaded successfully",
            "fixation_count": len(eye_events),
            "state": _get_state_payload(engine)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/state', methods=['GET'])
def api_state():
    """Get the current trial state (fixations, current index, etc.)."""
    engine = get_engine()
    return jsonify(_get_state_payload(engine))

@app.route('/api/action/move', methods=['POST'])
def api_action_move():
    """Trigger the core engine iterator to navigate forward or backwards."""
    data = request.json or {}
    direction = data.get('direction')
    
    engine = get_engine()
    if direction == 'right' or direction == 'next':
        engine.next_fixation()
    elif direction == 'left' or direction == 'previous':
        engine.previous_fixation()
        
    return jsonify({
        "message": f"Moved {direction}",
        "state": _get_state_payload(engine)
    })

# Helper to format state for JSON
def _get_state_payload(engine):
    payload = {
        "has_data": engine.eye_events is not None and not engine.eye_events.empty,
        "current_fixation": engine.current_fixation,
        "fixations": [],
        "saccades": [] # Could be computed here or on frontend
    }
    
    if payload["has_data"]:
        # We only send fixation events to frontend to build UI
        fix_df = engine.eye_events[engine.eye_events['eye_event'] == 'fixation']
        cols = ['x_cord', 'y_cord', 'duration']
        payload["fixations"] = fix_df[cols].to_dict(orient='records')
        
    return payload



if __name__ == '__main__':
    print("Fix8 Web Server Starting...")
    print("Serving from:", os.path.dirname(os.path.abspath(__file__)))
    app.run(debug=True, port=5000)
