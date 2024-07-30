#!/usr/bin/python3.11

import os
import csv
import yaml
from jinja2 import Template
from datetime import datetime, timedelta


def clean_slate():

    applied_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/config_files/applied_configs")
    generated_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/config_files/generated_configs")

    applied_config_files = []
    for file in os.listdir(applied_configs_path):
        file_path = os.path.join(applied_configs_path, file)
        if os.path.isfile(file_path):
            applied_config_files.append(file)
            os.remove(file_path)

    generated_config_files = []
    for file in os.listdir(generated_configs_path):
        file_path = os.path.join(generated_configs_path, file)
        if os.path.isfile(file_path):
            generated_config_files.append(file)
            os.remove(file_path)

    hosts_file_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/hosts.yml")

    if os.path.exists(hosts_file_path):
        os.remove(hosts_file_path)


##################################################################################################################
        

def create_hosts_file():

    #cwd = os.path.abspath(os.path.dirname(__file__))

    main_csv = os.path.expanduser("~/ansible/ansible_playbooks/refresh/main.csv")
    generated_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/config_files/generated_configs")
    hosts_file_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/hosts.yml")
    vsf_device_info_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/vsf_info.csv")

    device_info = {}
    firmware_update_device_info = {}

    with open(main_csv) as f:
        main_csv_opened = csv.DictReader(f)
        for row in main_csv_opened:
            switch_hostname = row["switch_hostname"]
            prov_ip = row["prov_ip"]
            switch_model = row['switch_model']

            device_info[switch_hostname] = {"ansible_host": prov_ip}
            #device_info[switch_hostname]['switch_model'] = int(switch_model)
            firmware_update_device_info[switch_hostname] = {"ansible_host": prov_ip}
            firmware_update_device_info[switch_hostname]['switch_model'] = int(switch_model)


    ansible_inventory = {
        'MAIN': {
            'hosts': {},
        },
        'FIRMWARE_UPDATE': {
            'hosts':{},
        }
    }

    with open(vsf_device_info_path) as f:
        vsf_info = csv.DictReader(f)
        for row in vsf_info:
            switch_hostname = row["switch_hostname"]
            prov_ip = row["prov_ip"]
            switch_model = row['switch_model']
            vsf_type = row['member_type']
            
            if vsf_type != 'conductor':
                firmware_update_device_info[switch_hostname] = {"ansible_host": prov_ip}
                firmware_update_device_info[switch_hostname]['switch_model'] = int(switch_model)


    for device, info in device_info.items():

        # generated_configs_path = os.path.join(cwd, "generated_configs")
        for file in os.listdir(generated_configs_path):
            # grab the filename of each file
            filename = os.path.basename(file)

            if device in filename:  # check if device name is in the filename
                config_file_path = os.path.join(generated_configs_path, file)
                info['config_file'] = config_file_path

                # adding global variables to each device
                ansible_inventory.setdefault('MAIN', {}).setdefault('vars', {})['ansible_connection'] = 'network_cli'
                ansible_inventory.setdefault('MAIN', {}).setdefault('vars', {})['ansible_network_os'] = 'arubanetworks.aoscx.aoscx'
                ansible_inventory['MAIN']['hosts'][device] = info

                break  # exit loop once the file is found for the device
        else:
            print(f"ERROR: no config file found for {device}")


    for device,info in firmware_update_device_info.items():
            ansible_inventory['FIRMWARE_UPDATE']['hosts'][device] = info
            ansible_inventory.setdefault('FIRMWARE_UPDATE', {}).setdefault('vars', {})['ansible_connection'] = 'network_cli'
            ansible_inventory.setdefault('FIRMWARE_UPDATE', {}).setdefault('vars', {})['ansible_network_os'] = 'arubanetworks.aoscx.aoscx'



    with open(hosts_file_path, 'w') as file:
        file.write ('---\n')
        yaml.dump(ansible_inventory, file, default_flow_style=False)



#############################################################################################################################################################

def create_scedule_reboot():

    # Get current date and time
    current_datetime = datetime.now()

    # Format the date and time as per your specific format
    clock_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    schedule_datetime = current_datetime + timedelta(seconds=45)
    schedule_datetime = schedule_datetime.replace(microsecond=0,second=0)
    schedule_datetime = schedule_datetime.strftime("%H:%M %Y-%m-%d")

    #loads in the j2 and csv files
    schedule_reboot_j2 = os.path.expanduser("~/ansible/ansible_playbooks/refresh/j2_templates/schedule_reboot.j2")
    main_csv = os.path.expanduser("~/ansible/ansible_playbooks/refresh/main.csv")
    generated_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/config_files/generated_configs")

    with open(schedule_reboot_j2) as f:
        schedule_reboot_template = Template(f.read(), keep_trailing_newline=True)


    with open(main_csv) as f:
        main_csv_opened = csv.DictReader(f)
        for row in main_csv_opened:

            switch_hostname = row["switch_hostname"]

            #generate the interface configuration for this row using the Jinja template
            schedule_reboot_commands = schedule_reboot_template.render(
                trigger_time= schedule_datetime,
                clock= clock_datetime,
            )


            with open (os.path.join(generated_configs_path, f"{switch_hostname}_schedule_reboot.ios"), 'w') as f:
                f.write(schedule_reboot_commands)

#######################################################################################################################


def create_vsf_stacking_info():

    vsf_device_info_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/vsf_info.csv")
    hosts_file_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/hosts.yml")


    conductors = []
    standbys = []
    members = []
    all_vsf_devices = {}

    with open (vsf_device_info_path) as f:
        vsf_device_info = csv.DictReader(f)

        for row in vsf_device_info:
            vsf_device = row["prov_ip"]
            link_1 = row["link_1"]
            link_2 = row["link_2"]
            member_number = row["member_number"]
            member_type = row ["member_type"]
            stack_number = row["stack_number"]
            secondary_member = row["secondary_member"]
            switch_model = row["switch_model"]

            if member_type == "conductor":
                conductors.append(vsf_device)

            if member_type == "standby":
                standbys.append(vsf_device)
        
            if member_type == "member":
                members.append(vsf_device)

            if vsf_device:
                all_vsf_devices[vsf_device] = {"link_1": str(link_1) , 
                                            "link_2": str(link_2) , 
                                            "member_number": str(member_number) , 
                                            "stack_number": str(stack_number) , 
                                            "member_type": str(member_type), 
                                            "secondary_member": str(secondary_member), }
    ###############
    ansible_inventory = {
        'VSF_DEVICES': {
            'vars': {
                'ansible_connection': 'network_cli',
                'ansible_network_os': 'arubanetworks.aoscx.aoscx'
            },
            'children': {
                'conductors': {
                    'hosts': {}
                },
                'members': {
                    'hosts': {}
                }
            }
        }
    }

    for device, info in all_vsf_devices.items():
        # Check if device is in the conductors list
        if device in conductors:
            # Add device to the conductors group
            ansible_inventory['VSF_DEVICES']['children']['conductors']['hosts'][device] = info
        else:
            # Add device to the members group
            ansible_inventory['VSF_DEVICES']['children']['members']['hosts'][device] = info

        #if device:
        #    ansible_inventory['firmware_update']['hosts'][device] = info


    with open(hosts_file_path, 'a') as file:
        yaml.dump(ansible_inventory, file, default_flow_style=False)
        file.write ('...\n')


#############################################################################################################################################



def create_base_config():

    #cwd = os.path.abspath(os.path.dirname(__file__))
    main_csv = os.path.expanduser("~/ansible/ansible_playbooks/refresh/main.csv")
    j2s = os.path.expanduser("~/ansible/ansible_playbooks/refresh/j2_templates")
    generated_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/config_files/generated_configs")


    with open(main_csv) as f:
        base_config_csv_opened = csv.DictReader(f)
        device_configs = {}

        for row in base_config_csv_opened:
            device = row["switch_hostname"]
            switch_model = row["switch_model"]

            if device not in device_configs:
                device_configs[device] = ""
            
            if row["distro"].lower() in {"y", "yes", "true"}:
                base_config_j2 = os.path.join(j2s, f"prov_distro_template.j2")

            else:
                base_config_j2 = os.path.join(j2s, f"prov_{switch_model}-template.j2") 

            with open(base_config_j2) as f:
                config_template = Template(f.read(), keep_trailing_newline=True)


            #generate the interface configuration for this row using the Jinja template
            base_config = config_template.render(
                switch_hostname=row["switch_hostname"],
                mgmt_vlan=row["mgmt_vlan"],
                mgmt_vlan_name=row["mgmt_vlan_name"],
                mgmt_ip=row["mgmt_ip"],
                mgmt_ip_cidr=row["mgmt_ip_cidr"],
                gateway_ip=row["gateway_ip"],            
                snmp_location=row["snmp_location"],
                snmp_description=row['snmp_description']
            )
            #append this interface configuration to the configuration for this device
            device_configs[device] += base_config

        #save the interface configurations for each device to a separate file
        for device, config in device_configs.items():
            output_path = os.path.join(generated_configs_path, f"{device}_base_config.ios")
            with open(output_path, "w") as f:
                f.write(config)

#####################################################################################################################################
                

def main():

    clean_slate()
    create_base_config()
    create_scedule_reboot()
    create_hosts_file()
    create_vsf_stacking_info()

if __name__ == "__main__":
    main()