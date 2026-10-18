import subprocess
import sys
if sys.platform.startswith("win"):
    shutdown = "shutdown /s /t 0"
    reboot_cmd = "shutdown /r /t 0"
if sys.platform.startswith("linux"):
    shutdown = "shutdown now"
    reboot_cmd = "reboot"
def poweroff():
    subprocess.run(shutdown, shell=True)
def reboot():
    subprocess.run(reboot_cmd,shell=True)
