import os
import subprocess

def run_subprocess_silent(command, **kwargs):
    if (os.name == 'nt'):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs.setdefault('startupinfo', startupinfo)
    return subprocess.run(command, **kwargs)
