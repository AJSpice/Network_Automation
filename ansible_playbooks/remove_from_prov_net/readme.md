#
Remove Switches from the Provision Network:

1. Open the input.csv file and fill out the Switch Hostname, Prov IP, and desired Spanning Tree Priority to be configured
2. Run the ansible playbook to remove the devices from the Provision Network:
    ansible-playbook remove_from_prov.yml