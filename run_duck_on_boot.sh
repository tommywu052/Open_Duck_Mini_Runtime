#!/bin/bash

#exec > /home/raspberry/duck_boot.log 2>&1  # log stdout and stderr

LOGFILE="/home/raspberry/duck_runtime.log"
exec >> "$LOGFILE" 2>&1
echo "===== Starting run_duck_on_boot.sh at $(date) ====="


echo "Waiting for ALSA audio to initialize..."

# Wait until the sound card is ready (i2s or USB, whatever shows up in aplay)
while ! aplay -l | grep -q "card"; do
    echo "No sound card detected yet..."
    sleep 1
done

echo "Sound card found!"





# Activate the virtualenv (make sure 'workon' is available in non-interactive shell)
source /home/raspberry/.virtualenvs/open-duck-mini-runtime/bin/activate

# Wait for 3 seconds
sleep 3

# Run your command
python -u /home/raspberry/Open_Duck_Mini_Runtime/scripts/py-xiaozhi.py
#python /home/raspberry/Open_Duck_Mini_Runtime/scripts/v2_rl_walk_mujoco.py \
#    --onnx_model_path /home/raspberry/Open_Duck_Mini_Runtime/scripts/BEST_WALK_ONNX_2.onnx \
#    -p 32 --commands --cutoff_frequency 40
