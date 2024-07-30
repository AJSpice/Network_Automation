import os
import csv
import yaml
from jinja2 import Template
from datetime import datetime, timedelta

def clean_slate():

    generated_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/firmware_updates/generated_configs")

    generated_config_files = []
    for file in os.listdir(generated_configs_path):
        file_path = os.path.join(generated_configs_path, file)
        if os.path.isfile(file_path):
            generated_config_files.append(file)
            os.remove(file_path)

    hosts_file_path = os.path.expanduser("~/ansible/ansible_playbooks/firmware_updates/hosts.yml")

    if os.path.exists(hosts_file_path):
        os.remove(hosts_file_path)

def create_hosts_file():

    #cwd = os.path.abspath(os.path.dirname(__file__))

    main_csv = os.path.expanduser("~/ansible/ansible_playbooks/firmware_updates/main.csv")
    generated_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/firmware_updates/generated_configs")
    hosts_file_path = os.path.expanduser("~/ansible/ansible_playbooks/firmware_updates/hosts.yml")

    device_info = {}
    firmware_update_device_info = {}

    with open(main_csv) as f:
        main_csv_opened = csv.DictReader(f)
        for row in main_csv_opened:
            switch_hostname = row["hostname"]
            prov_ip = row["prov_ip"]
            switch_model = row['model']

            device_info[switch_hostname] = {"ansible_host": prov_ip}
            #device_info[switch_hostname]['switch_model'] = int(switch_model)
            firmware_update_device_info[switch_hostname] = {"ansible_host": prov_ip}
            firmware_update_device_info[switch_hostname]['switch_model'] = int(switch_model)

    #print (device_info)
    #print (firmware_update_device_info)

    ansible_inventory = {
        'FIRMWARE_UPDATE': {
            'hosts':{},
        }
    }


    for device,info in firmware_update_device_info.items():
            ansible_inventory['FIRMWARE_UPDATE']['hosts'][device] = info
            ansible_inventory.setdefault('FIRMWARE_UPDATE', {}).setdefault('vars', {})['ansible_connection'] = 'network_cli'
            ansible_inventory.setdefault('FIRMWARE_UPDATE', {}).setdefault('vars', {})['ansible_network_os'] = 'arubanetworks.aoscx.aoscx'



    with open(hosts_file_path, 'w') as file:
        file.write ('---\n')
        yaml.dump(ansible_inventory, file, default_flow_style=False)

def main():
    clean_slate()
    create_hosts_file()

if __name__ == "__main__":
    main()