import os
import glob
import json
import pandas as pd
from src.core import Fix8Core

def run_batch():
    """
    Headless batch processor demonstrating the Fix8 MVC Refactor API.
    Loads JSON trials directly into Fix8Core, mathematically distorts them,
    and exports them to CSV without ever spawning a Qt window.
    """
    print("Initializing Fix8Core Headless Batch Processor...\n")
    import time
    start_time = time.time()
    
    # Initialize Engine (Model) without the GUI
    engine = Fix8Core()
    
    target_dir = "datasets/starter_examples"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    json_files = glob.glob(os.path.join(target_dir, "*.json"))
    
    if not json_files:
        print(f"No JSON files found in {target_dir}")
        return
        
    for count, trial_path in enumerate(json_files, 1):
        filename = os.path.basename(trial_path)
        print(f"[{count}/{len(json_files)}] Processing {filename}...")
        
        # 1. READ RAW DATA (Mimicking UI parsing)
        with open(trial_path, "r", encoding="utf-8") as f:
            trial_data = json.load(f)
            
        x_cord = []
        y_cord = []
        duration = []
        
        if 'fixations' not in trial_data.keys():
            # old JSON format
            for key in trial_data:
                x_cord.append(trial_data[key][0])
                y_cord.append(trial_data[key][1])
                duration.append(trial_data[key][2])
        else:
            # new JSON format
            for fixation in trial_data["fixations"]:
                x_cord.append(fixation[0])
                y_cord.append(fixation[1])
                duration.append(fixation[2])
                
        eye_events = pd.DataFrame(columns=["x_cord", "y_cord", "duration"])
        eye_events["x_cord"] = x_cord
        eye_events["y_cord"] = y_cord
        eye_events["duration"] = duration
        eye_events["eye_event"] = "fixation"
        
        if 'time_stamps' in trial_data.keys():
            eye_events["time_stamp"] = trial_data["time_stamps"]
            
        # 2. INJECT INTO MVC ENGINE
        engine.eye_events = eye_events
        print(f"   -> Loaded {len(eye_events)} fixations. Applying Noise Filter (Threshold: 20)...")
        
        # 3. TRIGGER PURE MATHEMATICAL EXECUTION
        engine.apply_noise(threshold=20)
        
        # 4. SAVE RESULTS HEADLESSLY
        output_path = os.path.join(output_dir, filename.replace(".json", "_noise_batch_export.csv"))
        engine.eye_events.to_csv(output_path, index=False)
        print(f"   -> Successfully saved exported data to {output_path}")

    end_time = time.time()
    print(f"\nBatch Processing 100% Complete! System Exiting cleanly.")
    print(f"Total time elapsed: {end_time - start_time:.4f} seconds!")

if __name__ == "__main__":
    run_batch()
