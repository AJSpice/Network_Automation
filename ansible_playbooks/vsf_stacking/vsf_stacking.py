#!/usr/bin/env python
import netmiko
import os
import csv
import yaml
from netmiko import ConnectHandler

cwd = os.getcwd()
vsf_device_info_path = os.path.join(cwd , "vsf_device_info.csv")
generated_configs_path = os.path.join(cwd, "generated_configs")


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
                                           "secondary_member": str(secondary_member)}


###############
ansible_inventory = {
    'PROV_NET': {
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
        ansible_inventory['PROV_NET']['children']['conductors']['hosts'][device] = info
    else:
        # Add device to the members group
        ansible_inventory['PROV_NET']['children']['members']['hosts'][device] = info

with open('hosts.yml', 'w') as file:
    file.write ('---\n')
    yaml.dump(ansible_inventory, file, default_flow_style=False)
    file.write ('...\n')

