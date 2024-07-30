#
import os
from jinja2 import Template
import csv
from getpass import getpass
from netmiko import ConnectHandler
from termcolor import colored, cprint

week_number = input("What week number is this for?\n")

username = input("\nWhat is the TACACS username?\n")
password = getpass("\nEnter TACACS Password\n")

site_mgmt_ips = []
site_routers = {}

def pull_info(week_number):

        
    # load in the file paths
    cwd = os.getcwd()
    info_main_log_file = os.path.join(cwd , "log_files" , f"week{week_number}" , f"info_week{week_number}.ios")

    with open(info_main_log_file , 'w') as f:
        f.write(f"WEEK {week_number}\n\n")

    # open the csv and parse the info - write to a unique config file
    with open (os.path.join(cwd , "csv_files" , f"ospf_migration_week{week_number}.csv"), "r") as f:

        ospf_migration_csv = csv.DictReader(f)


        for row in ospf_migration_csv:

            hostname = row["Hostname"]
            mgmt_ip = row["IP Address"]
                
                
            with open(info_main_log_file , 'a') as f:
                f.write(f"------------------------------------------------------------------------------------------------------------------------------\n")
                f.write(f"{hostname}\n\n")

            # init a blank config list
            config_commands = []

            # load in the pull info commands
            pull_info_commands = os.path.join(cwd ,"j2s" , "pull_info.j2")

            with open(pull_info_commands , "r") as f:
                for line in f:
                    config_commands.append(line)

            # setup the session details for the routers
            cisco_router = {
            'device_type': 'cisco_ios',
            'host': mgmt_ip,
            'username': username,
            'password': password,
            }

            try:
                net_connect = ConnectHandler(**cisco_router)
                net_connect.enable()
                cli_output = net_connect.send_config_set(config_commands , cmd_verify=False)
                with open (info_main_log_file , "a") as log_file:
                    log_file.write(f"\n{cli_output}")
                    log_file.write("\n\n")
                #cprint(cli_output , "green")
                net_connect.disconnect()
            
            except Exception as e:
                cprint(f"Error sending commands to {mgmt_ip}: {e}" , "red")


def main():
    pull_info(week_number=week_number)


if __name__ == "__main__":
    main()