import netmiko
from getpass import getpass
import logging
from netmiko import ConnectHandler
import os
import yaml
from datetime import datetime, timedelta
from jinja2 import Template
from termcolor import colored, cprint

cwd = os.getcwd()
hosts_file_path = os.path.join(cwd , "./hosts.yml")
generated_configs_path = os.path.join(cwd , "./config_files/generated_configs")

def read_ansible_inventory():

    # create hosts using the ansible hosts file
    with open (hosts_file_path) as hosts_file:
        data = yaml.safe_load(hosts_file)

    all_hosts = data["MAIN"]['hosts']

    return all_hosts

def create_scedule_reboot():

    # Get current date and time
    current_datetime = datetime.now()

    # Format the date and time as per your specific format
    clock_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    schedule_datetime = current_datetime + timedelta(seconds=120)
    schedule_datetime = schedule_datetime.replace(microsecond=0,second=0)
    schedule_datetime = schedule_datetime.strftime("%H:%M %Y-%m-%d")

    #loads in the j2 and csv files
    schedule_reboot_j2 = os.path.join(cwd, "./config_files/j2_templates/schedule_reboot.j2")
    #main_csv = os.path.expanduser("~/ansible/ansible_playbooks/refresh/main.csv")
    #generated_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/config_files/generated_configs")

    with open(schedule_reboot_j2) as f:
        remove_from_prod_template = Template(f.read(), keep_trailing_newline=True)

        #generate the interface configuration for this row using the Jinja template
        remove_from_prov_commands = remove_from_prod_template.render(
            trigger_time= schedule_datetime,
            clock= clock_datetime,
        )


    with open (os.path.join(generated_configs_path, f"schedule_reboot.ios"), 'w') as f:
        f.write(remove_from_prov_commands)

def reboot_all_hosts(all_hosts):
    #########

    config_commands = ""

    with open (os.path.join(cwd , "./config_files/generated_configs/schedule_reboot.ios"), 'r' ) as f:

        for line in f:
            config_commands += line 

    username = input("Username: ")
    password = getpass()

    # setup logging to a log file, first remove log file
    for file in os.listdir(cwd):
        file_path = os.path.join(cwd, file)
        if os.path.isfile(file_path):
            if "reboot_cli_logs" in file_path:
                os.remove(file_path)

    logging.basicConfig(filename='a_reboot_cli_logs', level=logging.DEBUG)
            
    for device_ip in all_hosts.keys():

        # setup the session details for this device
        aruba_10_10_1020 = {
        'device_type': 'aruba_osswitch',
        'ip': device_ip,
        'username': username,
        'password': password,
        #"read_timeout_override": 90,
        }
        
        # start connection to the device
        net_connect = ConnectHandler(**aruba_10_10_1020)

        try:
            net_connect.enable()
            net_connect.config_mode()
            cli_output = net_connect.send_config_set(config_commands , cmd_verify=False)
            #cli_output += net_connect.send_command("exit" , cmd_verify=False)
            cli_output += net_connect.send_command("boot set-default primary" , cmd_verify=False)
            cli_output += net_connect.send_command("sh schedule" , expect_string= '#')
            
            if "Enabled" and "Yes" in cli_output:
                cprint (f"\n{device_ip} successfully received the Schedule Reboot", "green")
            else:
                cprint (f"\n{device_ip} did not receive the Schedule Reboot" , "red")

            #print (cli_output)
        except Exception as e:
            cprint (f"Error sending commands to {device_ip}: {e}" , "red")


        net_connect.disconnect()

def main():
    
    all_hosts = read_ansible_inventory()
    ###########################################
    create_scedule_reboot()
    ###########################################
    reboot_all_hosts(all_hosts)

if __name__ == "__main__":
    main()