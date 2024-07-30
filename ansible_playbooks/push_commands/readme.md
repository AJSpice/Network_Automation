This script is used to send commands over SSH to targeted inventory. 


To modify affected hosts:

1. Open the hosts.yml file and follow the templating in ~/playbook_template.yml
2. Open the commands.ios file and modify the contents to CLI syntax and spacing for desired commands
3. Run the ansible-playbook to push the commands to all hosts in the hosts file:
    ansible-playbook push_commands.yml