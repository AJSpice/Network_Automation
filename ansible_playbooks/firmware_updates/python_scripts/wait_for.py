import subprocess
import time
import yaml
import os

cwd  = os.getcwd()

hosts_file_path = os.path.expanduser("~/ansible/ansible_playbooks/firmware_updates/hosts.yml")

with open (hosts_file_path) as hosts_file:
    data = yaml.safe_load(hosts_file)

main_hosts = data["FIRMWARE_UPDATE"]['hosts']

def ping_ip(ip_address):
    for attempt in range(1, 72):
        try:
            # Use subprocess to ping the IP address
            result = subprocess.call(['ping', '-c', '1', ip_address], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result == 0:
                print(f"{ip_address} is reachable")
                break
            else:
                print(f"{ip_address} is not responding (attempt {attempt})")
                time.sleep(10)  # Wait for 10 seconds before the next attempt
        except subprocess.CalledProcessError:
            print(f"Error while pinging {ip_address}")
            break
    else:
        print(f"{ip_address} failed after 72 attempts")

for host in main_hosts:
    ip_address = main_hosts[host]['ansible_host']
    ping_ip(ip_address)


time.sleep(40)  # Wait for 40 seconds to make sure the SSH connection will be ready