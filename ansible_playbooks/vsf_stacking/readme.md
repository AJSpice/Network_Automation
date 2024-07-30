#
#
VSF Stacking:

    1. Open and modify the vsf_device_info.csv file to the information for the switch(es) being modified
        Example vsf_device_info.csv file (using the "edit CSV" recommended extension) :
        
        
    2. Save the vsf_device_info.csv file and its changes
    3. Inside a terminal window, and inside the ~/ansible/ansible_playbooks/vsf_stacking directory run the push_vsf_config.yml playbook:
        ansible-playbook push_vsf_config.yml

Wait for the playbook to finish running and confirm the new stacking configuration on the switch(es)