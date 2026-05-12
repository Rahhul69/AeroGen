from flask import Flask, render_template, jsonify
import numpy as np
import pandas as pd
import os

app = Flask(__name__)

SAMPLING_RATE = 1000
DURATION = 100
TOTAL_ROWS = SAMPLING_RATE * DURATION

# This holds the generated data in RAM so it doesn't write to disk immediately
global_memory = {}

def create_turbine_dataframe(turbine_id, profile_name):
    time = np.linspace(0, DURATION, TOTAL_ROWS)
    base_rpm = 1500
    rpm = np.full(TOTAL_ROWS, base_rpm) + np.random.normal(0, 5, TOTAL_ROWS)
    vibration = np.sin(2 * np.pi * 25 * time) 
    
    if profile_name == "baseline":
        noise = np.random.normal(0, 0.1, TOTAL_ROWS)
    elif profile_name == "high_wind":
        noise = np.random.normal(0, 0.6, TOTAL_ROWS)
        rpm += np.sin(2 * np.pi * 0.2 * time) * 120 
    elif profile_name == "blade_pitch_error":
        noise = np.random.normal(0, 0.15, TOTAL_ROWS)
        vibration += np.sin(2 * np.pi * 50 * time) * 0.9 
    elif profile_name == "aging_bearing":
        noise = np.random.normal(0, 0.1, TOTAL_ROWS)
        vibration += np.linspace(0, 2.0, TOTAL_ROWS)
    elif profile_name == "unseen_test":
        noise = np.random.normal(0, 0.2, TOTAL_ROWS)
        fault_signal = np.zeros(TOTAL_ROWS)
        fault_signal[TOTAL_ROWS//2:] = np.sin(2 * np.pi * 50 * time[TOTAL_ROWS//2:]) * 1.5
        vibration += fault_signal

    # Return the dataframe instead of saving it
    return pd.DataFrame({"timestamp_sec": time, "vibration_g": vibration + noise, "rotor_rpm": rpm})

@app.route('/')
def index():
    return render_template('farm.html')

@app.route('/generate')
def generate():
    global global_memory
    global_memory.clear() # Clear any old data
    
    scenarios = [(1, "baseline"), (2, "high_wind"), (3, "blade_pitch_error"), (4, "aging_bearing"), (5, "unseen_test")]
    
    for t_id, profile in scenarios:
        df = create_turbine_dataframe(t_id, profile)
        filename = f"turbine_{t_id}_{profile}.csv"
        global_memory[filename] = df # Store in RAM
        
    return jsonify({"status": "ready"})

@app.route('/store')
def store():
    global global_memory
    if not global_memory:
        return jsonify({"status": "error", "message": "No data in memory."})
        
    # User confirmed. Write RAM to Hard Drive.
    for filename, df in global_memory.items():
        df.to_csv(filename, index=False)
        
    return jsonify({"status": "saved"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)