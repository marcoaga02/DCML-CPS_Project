#!/bin/bash

# function to stress the RAM
stress_ram() {
    echo "Stressing RAM: 90% with 2 threads for 20 seconds..."
    stress-ng --vm 2 --vm-bytes 90% --timeout 20s
}

# function to stress the CPU
stress_cpu() {
    local cores=$1
    echo "Stressing CPU: $cores cores for 20 seconds..."
    stress-ng --cpu $cores --timeout 20s
}

# Function to stress both CPU and RAM at the same time
stress_mixed() {
    local cpu_cores=$1
    echo "Stressing CPU ($cpu_cores cores) and RAM (80%) for 20 seconds..."
    stress-ng --cpu $cpu_cores --vm 1 --vm-bytes 80% --timeout 20s
}

echo "==============================="
echo "Starting a new stress cycle..."
echo "==============================="

stress_ram

echo "Cooling down for 10 seconds..." # Cooling down step after each stress cycle
sleep 10

stress_cpu 1 # stress one core of the CPU

echo "Cooling down for 10 seconds..." # Cooling down step after each stress cycle
sleep 10

total_cores=$(nproc)
stress_cpu $total_cores # stress all cores of the CPU

echo "Cooling down for 10 seconds..." # Cooling down step after each stress cycle
sleep 10

stress_mixed $((total_cores / 2)) # Using half of the total number of cores, stress both RAM and CPU

echo "==========================="
echo "End of the stress cycle..."
echo "==========================="
