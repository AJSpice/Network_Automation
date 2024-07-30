import os
from jinja2 import Template
import csv
import yaml

cwd = os.getcwd()
generated_configs_path = os.path.join(cwd, "generated_configs")
hosts_yml_file = os.path.join(cwd , "hosts.yml")


#loads in the j2 and csv files
wap_config_j2 = os.path.join(cwd, "wap_config.j2")
base_config_csv = os.path.join(cwd, "wap_info.csv")


generated_config_files = []
for file in os.listdir(generated_configs_path):
    file_path = os.path.join(generated_configs_path, file)
    if os.path.isfile(file_path):
        generated_config_files.append(file)
        os.remove(file_path)

os.remove(hosts_yml_file)


with open(wap_config_j2) as f:
    config_template = Template(f.read(), keep_trailing_newline=True)

with open(base_config_csv) as f:
    base_config_csv_opened = csv.DictReader(f)
    #create a dictionary to store the interface configurations for each device
    device_configs = {}
    for row in base_config_csv_opened:
        device = row["switch_ip"]
        #create a new entry in the dictionary for each device, if it doesn't exist already
        if device not in device_configs:
            device_configs[device] = ""
        #generate the interface configuration for this row using the Jinja template
        wap_config = config_template.render(
            wap_name=row["wap_name"],            
            native_vlan=row["native_vlan"],
            switchport = row["switchport"],
        )
        #append this interface configuration to the configuration for this device
        device_configs[device] += wap_config

    #save the interface configurations for each device to a separate file
    for device, config in device_configs.items():
        output_path = os.path.join(cwd, "generated_configs", f"{device}_wap_config.ios")
        with open(output_path, "w") as f:
            f.write(config)

device_info = {}

wap_info_csv = os.path.join(cwd, "wap_info.csv")

with open(wap_info_csv) as f:
    device_info_csv = csv.DictReader(f)
    for row in device_info_csv:
        #switch_hostname = row["switch_hostname"]
        switch_ip = row["switch_ip"]

        device_info[switch_ip] = {"ansible_host": switch_ip}
    
ansible_inventory = {
    'MAIN': {
        'hosts': {},
    }
}

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

with open('hosts.yml', 'w') as file:
    file.write ('---\n')
    yaml.dump(ansible_inventory, file, default_flow_style=False)
    file.write ('...\n')

#write the inventory to a file in YAML format


####
####