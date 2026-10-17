import subprocess
import sys
if sys.platform.startswith("win"):
    shutdown = "shutdown /s /t 0"
    reboot = "shutdown /r /t 0"
if sys.platform.startswith("linux"):
    shutdown = "shutdown now"
    reboot = "reboot"
def poweroff():
    subprocess.run([shutdown])
def reboot():
    subprocess.run([reboot])
