import subprocess
import time
import yaml
import os
from termcolor import colored, cprint
from datetime import datetime, timedelta
############################################################################

# get variable contents
cwd  = os.getcwd()
current_datetime = datetime.now()
reboot_max_time_delta = current_datetime + timedelta(minutes=5)
online_max_time_delta = current_datetime + timedelta(minutes=35)

# global variables
current_datetime = current_datetime.strftime("%H%M%S")
reboot_max_time_delta = reboot_max_time_delta.strftime("%H%M%S")
online_max_time_delta = online_max_time_delta.strftime("%H%M%S")
hosts_file_path = os.path.join(cwd , "hosts.yml")

# init the empty dictionaries
rebooted_switches = {}
finished_switches = {}

##########################################################################

def read_ansible_inventory():

    # create hosts using the ansible hosts file
    with open (hosts_file_path) as hosts_file:
        data = yaml.safe_load(hosts_file)

    all_hosts = data["MAIN"]['hosts']

    return all_hosts

def wait_for_disconnect(ip_address):
    try:
        result = subprocess.call(['ping', '-c', '1', ip_address], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if result == 0:
            time.sleep(1)
        else:
            time.sleep(1)

    except subprocess.CalledProcessError:
       print(f"Error while pinging {ip_address}")

    return result

def wait_for_connection(ip_address):
    try:
        result = subprocess.call(['ping', '-c', '1', ip_address], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        
        if result == 0:
            time.sleep(1)
        else:
            time.sleep(1)

    except subprocess.CalledProcessError:
       print(f"Error while pinging {ip_address}")

    return result

def wait_for_reboot(all_hosts):
    while True:
        current_datetime = datetime.now()
        current_datetime = current_datetime.strftime("%H%M%S")

        if current_datetime > reboot_max_time_delta:
            break

        else:

            if rebooted_switches.keys() != all_hosts.keys():

                for host_ip,blank in all_hosts.items():
                        try:
                            ping_result = wait_for_connection(host_ip)

                            if ping_result == 1:
                                cprint(f"{host_ip} is OFFLINE", 'red')
                                rebooted_switches[host_ip] = {}

                            else:
                                cprint(f"{host_ip} is still responding", 'green')
                        
                        
                        except subprocess.CalledProcessError:
                            print(f"Error while pinging {host_ip}")

            else:
                break

def wait_for_finish(all_hosts):

    while True:
        current_datetime = datetime.now()
        current_datetime = current_datetime.strftime("%H%M%S")

        if current_datetime > online_max_time_delta:
            break
        
        else:

            if finished_switches.keys() != all_hosts.keys():

                for host_ip in rebooted_switches.keys():
                        try:
                            ping_result = wait_for_connection(host_ip)

                            if ping_result == 0:
                                cprint(f"{host_ip} is back ONLINE", 'green')
                                finished_switches[host_ip] = {}

                            else:
                                cprint(f"{host_ip} is not responding", 'red')
                        
                        
                        except subprocess.CalledProcessError:
                            print(f"Error while pinging {host_ip}")
            else:
                break

def final_pings(ip_address):
    try:
        result = subprocess.call(['ping', '-c', '1', ip_address], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if result == 0:
            time.sleep(1)
            cprint (f"{ip_address} PASSES FINAL PING", 'green')
        else:
            time.sleep(1)
            cprint(f"{ip_address} HAS FAIELD FINAL PING" , 'red')

    except subprocess.CalledProcessError:
        print(f"Error while pinging {ip_address}")

    return result


def main():
    #
    all_hosts = read_ansible_inventory()
    #
    print ("\n\n")
    wait_for_reboot(all_hosts)
    
    ##########################################################
    print ("\n\nALL SWITCHES OFFLINE")
    print ("WAITING FOR SWITCHES TO COME BACK ONLINE\n\n")
    #########################################################

    wait_for_finish(all_hosts)
    #
    for i in range (1,6):

        for host_ip in all_hosts.keys():

            final_pings(host_ip)

if __name__ == "__main__":
    main()