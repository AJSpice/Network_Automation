##
# use nmap module to scan a given subnet and output it to a YAML file so it can be used as an Ansible hosts file
##
import nmap
import json
import yaml
import csv
import os


ansible_inventory = {
    'MAIN': {
        'hosts': {},
    }
}

def clean_slate():

    hosts_file_path = os.path.expanduser("~/ansible/ansible_playbooks/config_audits/client_track_ip/hosts.yml")
    nmap_output_path = os.path.expanduser("~/ansible/ansible_playbooks/config_audits/client_track_ip/nmap_output.json")

    if os.path.exists(hosts_file_path):
        os.remove(hosts_file_path)
    else:
        print (f"No hosts file found for path {hosts_file_path}")

    if os.path.exists(nmap_output_path):
        os.remove(nmap_output_path)
    else:
        print (f"No nmap_output file file found for path {nmap_output_path}")

def define_target_subnets():
    target_subnets = []

    with open ('target_subnets.csv' , 'r') as f:
        subnet_csv = csv.DictReader(f)
        for row in subnet_csv:
            subnet = row['subnet']

            target_subnets.append(subnet)

    return(target_subnets)

def main():

    target_subnets = define_target_subnets()

    nmap_results_list = []  # Initialize nmap_results_list

    for subnet in target_subnets:

        nm = nmap.PortScanner()
        #subnet_scan_results = nm.scan(subnet, '22-443')
        try:
            #subnet_scan_results = nm.scan(subnet, '22-443', arguments = '-T4 -A -v')
            subnet_scan_results = nm.scan(subnet, '443', arguments = '-T4 -A -v')

        except:
            print (f"Failure to scan subnet: {subnet}")
        #subnet_scan_results = nm[subnet].state()
        #subnet_scan_results = nm.command_line(f'nmap -T4 -A -v {subnet}')

        nmap_results_list.append(subnet_scan_results)  # Add the results of the current subnet scan to the list
        
        try:
            if (subnet_scan_results['nmap']['scaninfo']['error']):
                print (f'ERROR scanning subnet {subnet}')
        except:
            print (f'SUCCESS scanning subnet {subnet}')

        for host,details in subnet_scan_results['scan'].items():
            try:
                if details['status']['state'] == "up":  # check if device is online
                    if 'tcp' in details and 443 in details['tcp']:
                            if 'HPE' in details['tcp'][443]['script']['ssl-cert']:
                                print (f"{host} is likely an Aruba model and is being added to the hosts file")
                                ansible_inventory['MAIN']['hosts'][host] = {}
                            else:
                                continue
                    else:
                        print (f"{host} does not have the HPE flag and is not being added to the hosts file")
                        continue
                else:
                    continue
            except:
                print (f'Conditionals failed on host {host}')

    with open('hosts.yml', 'a') as file:
        ansible_inventory.setdefault('MAIN', {}).setdefault('vars', {})['ansible_connection'] = 'network_cli'
        ansible_inventory.setdefault('MAIN', {}).setdefault('vars', {})['ansible_network_os'] = 'arubanetworks.aoscx.aoscx'
        yaml.dump(ansible_inventory, file, default_flow_style=False)
        file.write ('...\n')

    with open ('nmap_output.json' , 'w') as f:
        json.dump(nmap_results_list , f)  # dump the entire list to the file

    return(nmap_results_list)  # Return the complete nmap_results_list after the loop


if __name__ == "__main__":
    clean_slate()
    define_target_subnets()
    main()