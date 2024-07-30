import subprocess
import os

cwd = os.getcwd()

scripts = [os.path.join(cwd , 'create_dynamic_inventory.py') , os.path.join(cwd , 'api_requests.py')]

for script in scripts:
    subprocess.call(['/bin/python3.11', script])