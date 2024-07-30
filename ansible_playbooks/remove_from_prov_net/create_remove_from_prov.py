import os
from jinja2 import Template
import csv
import yaml
from datetime import datetime, timedelta

cwd = os.getcwd()
generated_configs_path = os.path.join (cwd , "generated_configs")
input_csv = os.path.join(cwd, "input.csv")


generated_config_files = []
for file in os.listdir(generated_configs_path):
    file_path = os.path.join(generated_configs_path, file)
    if os.path.isfile(file_path):
        generated_config_files.append(file)
        os.remove(file_path)

# Get current date and time
current_datetime = datetime.now()

# Format the date and time as per your specific format
clock_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
schedule_datetime = current_datetime + timedelta(minutes=2)
schedule_datetime = schedule_datetime.replace(microsecond=0,second=0)
schedule_datetime = schedule_datetime.strftime("%H:%M %Y-%m-%d")

# loads in the j2 and csv files
remove_from_prov_j2 = os.path.join(cwd, "remove_from_prov.j2")
input_csv = os.path.join(cwd, "input.csv")


# create a j2 template by using the jinja template module
with open(remove_from_prov_j2) as f:
    remove_from_prod_template = Template(f.read(), keep_trailing_newline=True)

# open the input csv and create the config files
with open(input_csv) as f:
    input_csv_opened = csv.DictReader(f)
    for row in input_csv_opened:
        switch_hostname = row["switch_hostname"]

        # generate the configurations for this row using the Jinja template
        remove_from_prov_commands = remove_from_prod_template.render(
            prov_ip=row["prov_ip"],
            spanning_tree_priority=row["spanning_tree_priority"],
            trigger_time= schedule_datetime,
            clock= clock_datetime,
        )

        with open (os.path.join(generated_configs_path, f"{switch_hostname}_remove_from_prov.ios"), 'w') as f:
            f.write(remove_from_prov_commands)

device_info = {}

with open(input_csv) as f:
    device_info_csv = csv.DictReader(f)
    for row in device_info_csv:
        switch_hostname = row["switch_hostname"]
        prov_ip = row["prov_ip"]

        device_info[switch_hostname] = {"ansible_host": prov_ip}


#########################################################################################################
    

ansible_inventory = {
    'MAIN': {
        'hosts': {},
    }
}

for device, info in device_info.items():

    for file in os.listdir(generated_configs_path):

        # grab the filename of each file
        filename = os.path.basename(file)

        if device in filename:  # check if device name is in the filename
            config_file_path = os.path.join(generated_configs_path, file)
            info['config_file'] = config_file_path


            # adding global variables to each device
            ansible_inventory.setdefault('MAIN', {}).setdefault('vars', {})['ansible_connection'] = 'network_cli'
            ansible_inventory.setdefault('MAIN', {}).setdefault('vars', {})['ansible_network_os'] = 'arubanetworks.aoscx.aoscx'

            ansible_inventory.setdefault('MAIN', {}).setdefault('hosts', {})[device] = {}
            ansible_inventory.setdefault('MAIN', {}).setdefault('hosts', {})[device]['ansible_host'] = prov_ip
            ansible_inventory['MAIN']['hosts'][device] = info

            found_config = True
            break

        if not found_config:
            print(f"ERROR: no config file found for {device}")

with open('hosts.yml', 'w') as file:
    file.write ('---\n')
    yaml.dump(ansible_inventory, file, default_flow_style=False)
    file.write ('...\n')

####
####