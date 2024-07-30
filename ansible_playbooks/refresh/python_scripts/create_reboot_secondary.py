#
import os
from jinja2 import Template
from datetime import datetime, timedelta

def create_schedule_reboot_secondary():

    current_datetime = datetime.now()

    #format the date and time as per your specific format
    clock_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    schedule_datetime = current_datetime + timedelta(seconds=45)
    schedule_datetime = schedule_datetime.replace(microsecond=0,second=0)
    schedule_datetime = schedule_datetime.strftime("%H:%M %Y-%m-%d")

    #loads in the j2 and csv files
    schedule_reboot_secondary_j2 =  os.path.expanduser("~/ansible/ansible_playbooks/refresh/j2_templates/schedule_reboot_secondary.j2")
    #
    generated_configs_path = os.path.expanduser("~/ansible/ansible_playbooks/refresh/config_files/generated_configs")

    with open(schedule_reboot_secondary_j2) as f:
        schedule_reboot_secondary_template = Template(f.read(), keep_trailing_newline=True)

        schedule_reboot_commands = schedule_reboot_secondary_template.render(
            trigger_time= schedule_datetime,
            clock= clock_datetime,
        )


        with open (os.path.join(generated_configs_path, f"schedule_reboot_secondary.ios"), 'w') as f:
            f.write(schedule_reboot_commands)

def main():
    create_schedule_reboot_secondary()


if __name__ == "__main__":
    main()