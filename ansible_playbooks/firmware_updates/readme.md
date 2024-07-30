Firmware Updates:

    1. Modify the hosts.yml file in this directory to target switch(es) on the PROV_NET for firmware update (See Ansible page for more details)
    2. Save the hosts.yml file and its changes
    3. Inside a terminal window, and inside the ~/ansible/ansible_playbooks/firmware_updates directory run the firmware_update_{ model # of switch }.yml playbook:
        ansible-playbook firmware_update_{ model # of switch }.yml

Wait for the playbook to finish running and confirm the new firmware is loaded onto the switch(es)