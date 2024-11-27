import os
import subprocess

def get_git_hash():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'],cwd=os.path.dirname(os.path.realpath(__file__))).decode('ascii').strip()
    except:
        return None