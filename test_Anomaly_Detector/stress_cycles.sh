#!/bin/bash

echo "==============================="
echo "Starting a new stress cycle..."
echo "==============================="


echo "Stressing RAM with 2 threads for 20 seconds..."
stress-ng --vm 2 --vm-bytes 90% --timeout 20s

echo "Cooling down for 10 seconds..." # Cooling down step after each stress cycle
sleep 10

echo "Stressing few CPU cores for 15 seconds..."
stress-ng --cpu 2 --timeout 15s

echo "Cooling down for 10 seconds..." # Cooling down step after each stress cycle
sleep 10

echo "Stressing few cores CPU for 15 seconds..."
total_cores=$(nproc)
stress-ng --cpu $total_cores --timeout 15s

echo "Cooling down for 10 seconds..." # Cooling down step after each stress cycle
sleep 10

echo "Stressing both CPU and RAM for 15 seconds..."
stress-ng --cpu $((total_cores / 2)) --vm 1 --vm-bytes 80% --timeout 15s

echo "==========================="
echo "End of the stress cycle..."
echo "==========================="