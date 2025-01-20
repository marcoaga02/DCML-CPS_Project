#!/bin/bash

# Check if PID is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <PID>"
    exit 1
fi

PID=$1 # pid of the process to monitor
mkdir -p log
OUTPUT_FILE="log/intrusiveness_monitor.csv"

# Clear the log file and write the CSV header
echo "Timestamp,CPU (%),Memory VSZ (KB)" > $OUTPUT_FILE

# Monitor the process until it terminates
# the command ps -p $PID > /dev/null redirect the stdout into the "file" /dev/null, a sort of "black hole" that discards everything it receives, and
# to avoid errors when the process with pid $PID will terminate, the command 2>&1 redirect the stderr to the stdout, i.e. the file /dev/null
while ps -p $PID > /dev/null 2>&1; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    CPU=$(ps -p $PID -o %cpu --no-headers)
    MEM_VSZ=$(ps -p $PID -o vsz --no-headers)
    echo "$TIMESTAMP,$CPU,$MEM_VSZ" >> $OUTPUT_FILE
    sleep 1
done
