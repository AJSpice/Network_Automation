import os
from jinja2 import Template
import csv
import yaml

cwd = os.getcwd()
csvs = os.path.join(cwd, "csv_files")
j2s = os.path.join(cwd, "jinja_templates")
generated_configs_path = os.path.join(cwd, "generated_configs")
applied_configs_path = os.path.join(cwd, "applied_configs")

def prov_base_config_6300(output_dir):

    #loads in the j2 and csv files
    base_config_j2 = os.path.join(cwd, j2s, "prov_6300-template.j2")
    base_config_csv = os.path.join(cwd, csvs, "base_config.csv")

    with open(base_config_j2) as f:
        config_template = Template(f.read(), keep_trailing_newline=True)

    with open(base_config_csv) as f:
        base_config_csv_opened = csv.DictReader(f)
        #create a dictionary to store the interface configurations for each device
        device_configs = {}
        for row in base_config_csv_opened:
            device = row["switch_hostname"]
            #create a new entry in the dictionary for each device, if it doesn't exist already
            if device not in device_configs:
                device_configs[device] = ""
            #generate the interface configuration for this row using the Jinja template
            base_config = config_template.render(
                switch_hostname=row["switch_hostname"],
                mgmt_vlan=row["mgmt_vlan"],
                mgmt_vlan_name=row["mgmt_vlan_name"],
                mgmt_ip=row["mgmt_ip"],
                mgmt_ip_cidr=row["mgmt_ip_cidr"],
                gateway_ip=row["gateway_ip"],            
                system_location=row["system_location"]
            )
            #append this interface configuration to the configuration for this device
            device_configs[device] += base_config

        #save the interface configurations for each device to a separate file
        for device, config in device_configs.items():
            output_path = os.path.join(output_dir, f"{device}_base_config.aos")
            with open(output_path, "w") as f:
                f.write(config)

def clean_slate():
    
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

def get_device_info():
    device_info = {}

    base_config_csv = os.path.join(cwd, csvs, "base_config.csv")

    with open(base_config_csv) as f:
        device_info_csv = csv.DictReader(f)
        for row in device_info_csv:
            switch_hostname = row["switch_hostname"]
            prov_ip = row["prov_ip"]

            device_info[switch_hostname] = {"ansible_host": prov_ip}

    return device_info

def generate_ansible_inventory():
    
    ansible_inventory = {
        'MAIN': {
            'hosts': {},
        }
    }

    device_info = get_device_info()

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

                ansible_inventory.setdefault('MAIN', {}).setdefault('hosts', {})[device] = info
                ansible_inventory['MAIN']['hosts'][device] = info
                break  # exit loop once the file is found for the device
        else:
            print(f"ERROR: no config file found for {device}")

    return ansible_inventory

def create_ansible_inventory(ansible_inventory):
    with open('hosts.yml', 'w') as file:
        file.write ('---\n')
        yaml.dump(ansible_inventory, file, default_flow_style=False)
        file.write ('...\n')

def main():

    clean_slate()
    prov_base_config_6300(generated_configs_path)


main()

#generate the ansible inventory
inventory_data = generate_ansible_inventory()

#write the inventory to a file in YAML format
create_ansible_inventory(inventory_data)


####
####