#
#
Base Config:

    1. Open and modify the base_config.csv under the ./csv_files dir
    2. Save the base_config.csv and its changes
    3. Inside a terminal window, and inside the ~/ansible/ansible_playbooks_base_config directory run the push_{ model # of switch }_base_config.yml:
        ansible-playbook  push_{ model # of switch }_base_config.yml
    4. Wait for the playbook to finish running and confirm the new base configs are applied to the switches
        Confirm configs by comparing ./applied_configs to ./generated_configs