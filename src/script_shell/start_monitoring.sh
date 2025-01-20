#!/bin/bash

# Starts the python process in background
python3 src/main_anomaly_detector.py &
PYTHON_PID=$!

# Starts the intrusiveness monitoring process
./src/script_shell/intrusiveness_monitor.sh $PYTHON_PID
