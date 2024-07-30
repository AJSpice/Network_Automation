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

cwd = os.getcwd()
main_log_file = os.path.join(cwd , "log_files" , f"week{week_number}" , f"week{week_number}main.ios")
with open(main_log_file , 'w') as f:
    f.write("----------------------------------------------------------------\n")

site_routers = {}

def generate_ospf_config_files(week_number):

        
    # load in the file paths
    cwd = os.getcwd()
    staff_and_public_ospf_jinja_template_path = os.path.join(cwd , "j2s" , "staff_and_public_ospf_config.j2")
    staff_only_ospf_jinja_template_path = os.path.join(cwd , "j2s" , "staff_ospf_config.j2")
    # staff_and_public_ospf_jinja_template_path = os.path.join(cwd , "j2s" , "test.j2")
    # staff_only_ospf_jinja_template_path = os.path.join(cwd , "j2s" , "test.j2")
    main_log_file = os.path.join(cwd , "log_files" , f"week{week_number}" , f"week{week_number}_main.ios")

    # create the ospf jinja template
    with open (staff_and_public_ospf_jinja_template_path) as f:
        # read the ospf jinja template file
        staff_and_public_ospf_config_template = Template(f.read(), keep_trailing_newline=True)

    with open (staff_only_ospf_jinja_template_path) as f:
        # read the ospf jinja template file
        staff_only_ospf_config_template = Template(f.read(), keep_trailing_newline=True)

    with open(main_log_file , 'a') as f:
        f.write(f"WEEK {week_number}\n\n")

    # open the csv and parse the info - write to a unique config file
    with open (os.path.join(cwd , "csv_files" , f"ospf_migration_week{week_number}.csv"), "r") as f:

        ospf_migration_csv = csv.DictReader(f)

        for row in ospf_migration_csv:

            hostname = row["Hostname"]

            device_unique_file_path = os.path.join(cwd , "generated_configs" , "individual_configs" , f"week{week_number}" , f"{hostname}_config_file.ios")

            # define the variables for staff PID
            ip_address = row["IP Address"]
            staff_router_id = row["Staff RTR ID"]
            staff_area_number = row["Staff Area #"]
            staff_wan_interface_number = row["Staff WAN int"]
            primary_staff_neighbor = row["Primary_Staff_Neighbor"]
            secondary_staff_neighbor = row["Secondary_Staff_Neighbor"]
            
            # define the variables for public PID
            public_router_id = row["Public RTR ID"]
            public_area_number = row["Public Area #"]
            public_wan_interface_number = row["Public WAN int"]
            primary_public_neighbor = row["Primary_Public_Neighbor"]
            secondary_public_neighbor = row["Secondary_Public_Neighbor"]


            if "N/A" not in public_area_number:

                # create a config file for Public PID and Staff PID ospf using the jinja template file
                ospf_config = staff_and_public_ospf_config_template.render(
                    public_rtr_id = public_router_id,
                    public_area = public_area_number,
                    public_wan_interface = public_wan_interface_number,
                    public_neighbor = primary_public_neighbor,
                    public_secondary_neighbor = secondary_public_neighbor,

                    staff_rtr_id = staff_router_id,
                    staff_area = staff_area_number,
                    staff_wan_interface = staff_wan_interface_number,
                    staff_neighbor = primary_staff_neighbor,
                    staff_secondary_neighbor = secondary_staff_neighbor
                )
            else:
                # create a config file for ONLY Staff PID ospf using the jinja template file
                ospf_config = staff_only_ospf_config_template.render(
                    public_rtr_id = public_router_id,
                    public_area = public_area_number,
                    public_wan_interface = public_wan_interface_number,
                    public_neighbor = primary_public_neighbor,
                    public_secondary_neighbor = secondary_public_neighbor,

                    staff_rtr_id = staff_router_id,
                    staff_area = staff_area_number,
                    staff_wan_interface = staff_wan_interface_number,
                    staff_neighbor = primary_staff_neighbor,
                    staff_secondary_neighbor = secondary_staff_neighbor
                )
            
            if "N/A" not in staff_area_number:
                
                # append the site mgmt to the list
                site_routers[hostname] = ip_address

                with open(device_unique_file_path , "w") as f:
                    f.write(ospf_config)
                
                with open(main_log_file , 'a') as f:
                    f.write(hostname)
                    f.write(f"{ospf_config}\n\n")


def push_ospf_config_files(username, password):

    cwd  = os.getcwd()

    for hostname,mgmt_ip in site_routers.items():

        config_file = os.path.join(cwd ,"generated_configs" , "individual_configs" , f"{hostname}_config_file.ios")
        config_commands = []

        with open(config_file , "r") as f:
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
            with open (os.path.join(cwd , "log_files" , f"week{week_number}_log_file.ios") , "a") as log_file:
                log_file.write(cli_output)
            #cprint(cli_output , "green")
            net_connect.disconnect()
        
        except Exception as e:
            cprint(f"Error sending commands to {mgmt_ip}: {e}" , "red")


def main():
    generate_ospf_config_files(week_number=week_number)
    #push_ospf_config_files(username=username , password=password)


if __name__ == "__main__":
    main()