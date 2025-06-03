# Xiaozhi speech control with duck mini

## Raspberry Pi 4 Used.

1.Copy all the files under this folder to ../scripts </BR>
2.Replace with the path related and mac address in py-xiaozhi.py</BR>
3.Clone ```led2812_flow.py``` from my repo to ../scripts <br>
4.Run ```python py-xiaozhi.py```

### You need to modify - ```v2_rl_walk_mujoco.py``` under ../scripts , check my repo from #218-#248
```
                    # speech-control - Override joystick input if simulating movement
                    if self.simulated_joystick == "forward":
                        self.last_commands[0] = 0.15  # forward
                        self.last_commands[1] = 0.0
                    elif self.simulated_joystick == "backward":
                        self.last_commands[0] = -0.15  # backward
                        self.last_commands[1] = 0.0
                    elif self.simulated_joystick == "left":
                        self.last_commands[0] = 0.0
                        self.last_commands[2] = -1  # turn left
                    elif self.simulated_joystick == "right":
                        self.last_commands[0] = 0.0
                        self.last_commands[2] = 1  # turn right

                    # speech-control - Override joystick input if head movement
                    if self.simulated_joystick == "headleftdown":
                        self.last_commands[4] = -0.1  # headleftdown
                        self.last_commands[6] = 0.3
                    elif self.simulated_joystick == "headrightdown":
                        self.last_commands[4] = -0.08  # headrightdown
                        self.last_commands[6] = -0.3
                    elif self.simulated_joystick == "headrotate":
                        self.last_commands[4] = -0.08
                        self.last_commands[5] = 0.25  # turn left
                        self.last_commands[6] = -0.05
                    elif self.simulated_joystick == "headup":
                        self.last_commands[4] = 0.25
                        self.last_commands[5] = -0.08  # turn right
                    elif self.simulated_joystick == "headdown":
                        self.last_commands[4] = -0.25
                        self.last_commands[5] = -0.08  # turn right
```

## Running as system service (Must to modify all your relative path to absolute path in python)
### Add new file (open-duck-mini.service.txt)
```sudo nano /etc/systemd/system/open-duck-mini.service```

### Add to service and start
sudo systemctl daemon-reexec <br>
sudo systemctl daemon-reload <bv>
sudo systemctl enable open-duck-mini.service <br>
sudo systemctl start open-duck-mini.service <br>

### ssh rpi4 to check the log
``` tail -f duck_runtime.log ```

### Modify your prompt as my prompt - ```xiaozhi-prompt.txt``` in the Xiaozhi backend


