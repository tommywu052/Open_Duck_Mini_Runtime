# Xiaozhi speech control with duck mini

## Raspberry Pi 4 Used.

1.Copy all the files under this folder to ../scripts </BR>
2.Replace with the path related and mac address in py-xiaozhi.py</BR>
3.Run ```python py-xiaozhi.py```

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


